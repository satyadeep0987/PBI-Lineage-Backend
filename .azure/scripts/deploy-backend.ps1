param(
    [Parameter(Mandatory = $true)]
    [string]$Image,

    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [Parameter(Mandatory = $false)]
    [string]$ContainerName = "pbi-lineage-api",

    [Parameter(Mandatory = $false)]
    [int]$HostPort = 8000,

    [Parameter(Mandatory = $false)]
    [int]$ContainerPort = 8000
)

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------
# Refresh machine PATH
# Azure Run Command may inherit an old PATH from the VM Agent.
# ------------------------------------------------------------

$MachinePath = [Environment]::GetEnvironmentVariable(
    "Path",
    "Machine"
)

$UserPath = [Environment]::GetEnvironmentVariable(
    "Path",
    "User"
)

$env:Path = "$MachinePath;$UserPath;$env:Path"

# ------------------------------------------------------------
# Resolve Docker executable explicitly
# ------------------------------------------------------------

$DockerCommand = Get-Command `
    "docker.exe" `
    -ErrorAction SilentlyContinue

if ($DockerCommand) {
    $DockerExe = $DockerCommand.Source
}
else {

    $DockerCandidates = @(
        "C:\Program Files\Docker\docker.exe",
        "C:\Program Files\docker\docker.exe"
    )

    $DockerExe = $DockerCandidates |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1
}

if (-not $DockerExe) {
    throw "docker.exe could not be located on the Azure VM."
}

Write-Host "Docker executable:"
Write-Host $DockerExe

# ------------------------------------------------------------
# Resolve Azure CLI explicitly
# ------------------------------------------------------------

$AzCommand = Get-Command `
    "az.cmd" `
    -ErrorAction SilentlyContinue

if (-not $AzCommand) {
    $AzCommand = Get-Command `
        "az.exe" `
        -ErrorAction SilentlyContinue
}

if ($AzCommand) {
    $AzExe = $AzCommand.Source
}
else {

    $AzCandidates = @(
        "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
        "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
    )

    $AzExe = $AzCandidates |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1
}

if (-not $AzExe) {
    throw "Azure CLI could not be located on the Azure VM."
}

Write-Host "Azure CLI executable:"
Write-Host $AzExe

Write-Host "========================================="
Write-Host "PBI Lineage Backend Deployment"
Write-Host "========================================="
Write-Host "Image: $Image"
Write-Host "Container: $ContainerName"

$AppRoot = "C:\pbi-lineage"
$DataRoot = Join-Path $AppRoot "data"
$LogRoot = Join-Path $AppRoot "logs"

foreach ($Directory in @(
    $AppRoot,
    $DataRoot,
    $LogRoot
)) {
    New-Item `
        -ItemType Directory `
        -Path $Directory `
        -Force | Out-Null
}

# ------------------------------------------------------------
# Production configuration
# ------------------------------------------------------------

$env:ENVIRONMENT = "production"
$env:LOG_LEVEL = "INFO"
$env:LINEAGE_DATABASE_PATH = "data/lineage.db"

$env:SNOWFLAKE_ALLOW_EXTERNAL_BROWSER_AUTH = "false"

# Pydantic list fields MUST remain valid JSON.
$env:CORS_ALLOWED_ORIGINS = '[]'

$env:ALLOWED_HOSTS = (
    '["lvpowerbilineage.com",' +
    '"www.lvpowerbilineage.com",' +
    '"localhost",' +
    '"127.0.0.1"]'
)

$env:FORCE_HTTPS = "false"
$env:ENABLE_API_DOCS = "false"

$env:AUTH_COOKIE_SECURE = "true"
$env:AUTH_COOKIE_SAMESITE = "lax"

# ------------------------------------------------------------
# Docker
# ------------------------------------------------------------

$DockerService = Get-Service `
    -Name docker `
    -ErrorAction SilentlyContinue

if (-not $DockerService) {
    throw "Docker Windows service was not found."
}

if ($DockerService.Status -ne "Running") {

    Write-Host "Starting Docker service..."

    Start-Service docker
}

$DockerReady = $false

for ($Attempt = 1; $Attempt -le 12; $Attempt++) {

    Write-Host "Docker readiness attempt $Attempt/12"

    & $DockerExe info *> $null

    if ($LASTEXITCODE -eq 0) {
        $DockerReady = $true
        break
    }

    Start-Sleep -Seconds 5
}

if (-not $DockerReady) {
    throw "Docker daemon did not become ready."
}

& $DockerExe version

if ($LASTEXITCODE -ne 0) {
    throw "Docker is not available."
}

# ------------------------------------------------------------
# VM Managed Identity -> ACR
# ------------------------------------------------------------

Write-Host "Authenticating VM managed identity..."

az login `
    --identity `
    --output none

if ($LASTEXITCODE -ne 0) {
    throw "VM managed identity login failed."
}

Write-Host "Authenticating to ACR..."

az acr login `
    --name $AcrName

if ($LASTEXITCODE -ne 0) {
    throw "ACR login failed."
}

Write-Host "Pulling image..."

& $DockerExe pull $Image

if ($LASTEXITCODE -ne 0) {
    throw "Failed to pull backend image."
}

# ------------------------------------------------------------
# Container helper
# ------------------------------------------------------------

function Start-BackendContainer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetImage
    )

    & $DockerExe run `
        --detach `
        --name $ContainerName `
        --restart unless-stopped `
        --publish "${HostPort}:${ContainerPort}" `
        --volume "${DataRoot}:C:\app\data" `
        --env ENVIRONMENT `
        --env LOG_LEVEL `
        --env LINEAGE_DATABASE_PATH `
        --env SNOWFLAKE_ALLOW_EXTERNAL_BROWSER_AUTH `
        --env CORS_ALLOWED_ORIGINS `
        --env ALLOWED_HOSTS `
        --env FORCE_HTTPS `
        --env ENABLE_API_DOCS `
        --env AUTH_COOKIE_SECURE `
        --env AUTH_COOKIE_SAMESITE `
        $TargetImage

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start backend container."
    }
}

function Test-BackendHealth {

    $LiveUrl = (
        "http://127.0.0.1:" +
        "$HostPort/api/v1/health/live"
    )

    $ReadyUrl = (
        "http://127.0.0.1:" +
        "$HostPort/api/v1/health/ready"
    )

    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {

        try {

            $Live = Invoke-WebRequest `
                -Uri $LiveUrl `
                -UseBasicParsing `
                -TimeoutSec 10

            $Ready = Invoke-WebRequest `
                -Uri $ReadyUrl `
                -UseBasicParsing `
                -TimeoutSec 10

            if (
                $Live.StatusCode -eq 200 -and
                $Ready.StatusCode -eq 200
            ) {
                return $true
            }
        }
        catch {
            Write-Host (
                "Health attempt $Attempt failed. " +
                "Retrying..."
            )
        }

        Start-Sleep -Seconds 5
    }

    return $false
}

# ------------------------------------------------------------
# Preserve previous deployment
# ------------------------------------------------------------

$PreviousImage = $null

$ExistingContainer = docker ps `
    -a `
    --filter "name=^/$ContainerName$" `
    --format "{{.ID}}"

if ($ExistingContainer) {

    $PreviousImage = docker inspect `
        --format "{{.Config.Image}}" `
        $ContainerName

    Write-Host "Previous image:"
    Write-Host $PreviousImage

    docker rm `
        --force `
        $ContainerName
}

# ------------------------------------------------------------
# Deploy
# ------------------------------------------------------------

try {

    Write-Host "Starting new backend container..."

    Start-BackendContainer `
        -TargetImage $Image

    Write-Host "Waiting for backend health..."

    if (-not (Test-BackendHealth)) {
        throw "Backend health validation failed."
    }

    Write-Host "Backend health checks passed."
}
catch {

    Write-Host ""
    Write-Host "New backend deployment failed."

    docker logs `
        --tail 200 `
        $ContainerName `
        2>$null

    docker rm `
        --force `
        $ContainerName `
        2>$null

    if ($PreviousImage) {

        Write-Host "Rolling back to:"
        Write-Host $PreviousImage

        Start-BackendContainer `
            -TargetImage $PreviousImage

        if (-not (Test-BackendHealth)) {
            throw (
                "New deployment failed and rollback " +
                "also failed health validation."
            )
        }

        Write-Host "Rollback completed successfully."
    }

    throw
}

Write-Host ""
Write-Host "Backend deployment completed successfully."
Write-Host "DEPLOYMENT_RESULT=SUCCESS"