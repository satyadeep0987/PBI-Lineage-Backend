param(
    [Parameter(Mandatory = $true)]
    [string]$Image,

    [Parameter(Mandatory = $false)]
    [string]$ContainerName = "pbi-lineage-api",

    [Parameter(Mandatory = $false)]
    [int]$HostPort = 8000,

    [Parameter(Mandatory = $false)]
    [int]$ContainerPort = 8000
)

$ErrorActionPreference = "Stop"

Write-Host "========================================="
Write-Host "PBI Lineage Backend Deployment"
Write-Host "========================================="
Write-Host "Image: $Image"
Write-Host "Container: $ContainerName"

$AppRoot = "C:\pbi-lineage"
$BackendRoot = Join-Path $AppRoot "backend"
$DataRoot = Join-Path $AppRoot "data"
$LogRoot = Join-Path $AppRoot "logs"

foreach ($Directory in @(
    $AppRoot,
    $BackendRoot,
    $DataRoot,
    $LogRoot
)) {
    if (-not (Test-Path $Directory)) {
        New-Item `
            -ItemType Directory `
            -Path $Directory `
            -Force | Out-Null
    }
}

Write-Host "Checking Docker..."

docker version

if ($LASTEXITCODE -ne 0) {
    throw "Docker is not available."
}

Write-Host "Pulling image..."

docker pull $Image

if ($LASTEXITCODE -ne 0) {
    throw "Failed to pull backend image."
}

$PreviousImage = $null

$ExistingContainer = docker ps `
    -a `
    --filter "name=^/$ContainerName$" `
    --format "{{.ID}}"

if ($ExistingContainer) {

    Write-Host "Existing container found."

    $PreviousImage = docker inspect `
        --format "{{.Config.Image}}" `
        $ContainerName

    Write-Host "Previous image: $PreviousImage"

    docker stop $ContainerName

    docker rm $ContainerName
}

Write-Host "Starting new backend container..."

docker run `
    --detach `
    --name $ContainerName `
    --restart unless-stopped `
    --publish "127.0.0.1:${HostPort}:${ContainerPort}" `
    --volume "${DataRoot}:C:\app\data" `
    $Image

if ($LASTEXITCODE -ne 0) {
    throw "Failed to start backend container."
}

Write-Host "Waiting for backend startup..."

Start-Sleep -Seconds 15

$HealthUrl = "http://127.0.0.1:$HostPort/api/v1/health/live"

try {

    $Response = Invoke-WebRequest `
        -Uri $HealthUrl `
        -UseBasicParsing `
        -TimeoutSec 15

    if ($Response.StatusCode -ne 200) {
        throw "Unexpected health status: $($Response.StatusCode)"
    }

    Write-Host "Backend health check passed."

}
catch {

    Write-Host "New deployment failed health validation."

    docker logs `
        --tail 200 `
        $ContainerName

    docker stop $ContainerName 2>$null
    docker rm $ContainerName 2>$null

    if ($PreviousImage) {

        Write-Host "Attempting rollback to $PreviousImage"

        docker run `
            --detach `
            --name $ContainerName `
            --restart unless-stopped `
            --publish "127.0.0.1:${HostPort}:${ContainerPort}" `
            --volume "${DataRoot}:C:\app\data" `
            $PreviousImage

        Write-Host "Rollback container started."
    }

    throw
}

Write-Host "Backend deployment completed successfully."