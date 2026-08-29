# escape=`

# ============================================================
# Stage 1 - Python + backend dependencies
# ============================================================

FROM mcr.microsoft.com/windows/servercore:ltsc2025 AS builder

SHELL ["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

WORKDIR C:\app

ENV UV_UNMANAGED_INSTALL="C:\uv"
ENV UV_PYTHON_INSTALL_DIR="C:\python"
ENV UV_PROJECT_ENVIRONMENT="C:\app\.venv"
ENV UV_CACHE_DIR="C:\uv-cache"
ENV UV_NO_MODIFY_PATH="1"

# ------------------------------------------------------------
# Install uv
# ------------------------------------------------------------

RUN Invoke-WebRequest `
        -UseBasicParsing `
        https://astral.sh/uv/0.12.6/install.ps1 `
        -OutFile C:\uv-install.ps1; `
    & C:\uv-install.ps1; `
    Remove-Item C:\uv-install.ps1 -Force; `
    & C:\uv\uv.exe --version; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ------------------------------------------------------------
# Install Python
# ------------------------------------------------------------

RUN & C:\uv\uv.exe python install 3.11.16; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ------------------------------------------------------------
# Install project dependencies
# ------------------------------------------------------------

COPY pyproject.toml uv.lock ./

RUN & C:\uv\uv.exe sync `
        --frozen `
        --no-dev `
        --no-install-project `
        --python 3.11.16; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ------------------------------------------------------------
# Verify Python dependencies
# ------------------------------------------------------------

RUN & 'C:\app\.venv\Scripts\python.exe' `
        -c 'import fastapi, uvicorn, httpx'; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; `
    Write-Host 'Python dependencies verified'


# ============================================================
# Stage 2 - Runtime
# ============================================================

FROM mcr.microsoft.com/windows/servercore:ltsc2025 AS runtime

SHELL ["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

WORKDIR C:\app

ENV PYTHONDONTWRITEBYTECODE="1"
ENV PYTHONUNBUFFERED="1"
ENV PYTHONUTF8="1"

# ------------------------------------------------------------
# Install MSOLAP
# ------------------------------------------------------------

ARG MSOLAP_MSI_URL

RUN if ([string]::IsNullOrWhiteSpace($env:MSOLAP_MSI_URL)) { `
        throw 'MSOLAP_MSI_URL build argument is required.' `
    }; `
    Write-Host 'Downloading MSOLAP...'; `
    Invoke-WebRequest `
        -UseBasicParsing `
        -Uri $env:MSOLAP_MSI_URL `
        -OutFile C:\msolap.msi; `
    Write-Host 'Installing MSOLAP...'; `
    $process = Start-Process `
        -FilePath 'msiexec.exe' `
        -ArgumentList '/i', 'C:\msolap.msi', '/qn', '/norestart' `
        -Wait `
        -PassThru; `
    Write-Host "MSOLAP installer exit code: $($process.ExitCode)"; `
    if (($process.ExitCode -ne 0) -and ($process.ExitCode -ne 3010)) { `
        throw "MSOLAP installation failed with exit code $($process.ExitCode)" `
    }; `
    Remove-Item C:\msolap.msi -Force

# ------------------------------------------------------------
# Copy Python and virtual environment from builder
# ------------------------------------------------------------

COPY --from=builder C:\python C:\python
COPY --from=builder C:\app\.venv C:\app\.venv

# ------------------------------------------------------------
# Copy backend
# ------------------------------------------------------------

COPY app .\app

# ------------------------------------------------------------
# Verify Python
# ------------------------------------------------------------

RUN & 'C:\app\.venv\Scripts\python.exe' --version; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ------------------------------------------------------------
# Verify backend dependencies
# ------------------------------------------------------------

RUN & 'C:\app\.venv\Scripts\python.exe' `
        -c 'import fastapi, uvicorn, httpx, win32com.client, pythoncom'; `
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; `
    Write-Host 'Runtime dependencies OK'

# ------------------------------------------------------------
# Verify ADODB COM
# ------------------------------------------------------------

RUN $connection = New-Object -ComObject ADODB.Connection; `
    if ($null -eq $connection) { `
        throw 'Unable to create ADODB.Connection COM object' `
    }; `
    Write-Host 'ADODB COM OK'

# ------------------------------------------------------------
# Verify MSOLAP registration
# ------------------------------------------------------------

RUN $providers = @( `
        Get-ChildItem `
            'HKLM:\SOFTWARE\Classes' `
            -ErrorAction SilentlyContinue `
        | Where-Object { $_.PSChildName -like 'MSOLAP*' } `
    ); `
    if ($providers.Count -eq 0) { `
        throw 'MSOLAP provider was not registered correctly.' `
    }; `
    Write-Host 'MSOLAP registration verified'; `
    $providers | Select-Object -ExpandProperty PSChildName

EXPOSE 8000

CMD ["C:\\app\\.venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]