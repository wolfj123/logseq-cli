[CmdletBinding()]
param(
    [switch]$TestPyPI,
    [string]$EnvFile = ".env.pypi"
)

$ErrorActionPreference = "Stop"

function Load-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    foreach ($rawLine in Get-Content -LiteralPath $Path) {
        $line = $rawLine.Trim()

        if (-not $line -or $line.StartsWith("#")) {
            continue
        }

        $parts = $line -split "=", 2
        if ($parts.Count -ne 2) {
            throw "Invalid dotenv line in '$Path': $rawLine"
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        Set-Item -Path "Env:$key" -Value $value
    }
}

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

Require-Command -Name "python"

$resolvedEnvFile = Join-Path $repoRoot $EnvFile
if (Test-Path -LiteralPath $resolvedEnvFile) {
    Load-DotEnv -Path $resolvedEnvFile
}

if (-not $env:TWINE_USERNAME) {
    $env:TWINE_USERNAME = "__token__"
}

if (-not $env:TWINE_PASSWORD) {
    throw "Missing TWINE_PASSWORD. Set it in the environment or add it to '$EnvFile'."
}

Write-Host "Publishing version from pyproject.toml without changing it."

Remove-Item -Recurse -Force ".\dist" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\build" -ErrorAction SilentlyContinue
Get-ChildItem -Force -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

python -m build
python -m twine check .\dist\*

if ($TestPyPI) {
    python -m twine upload --repository testpypi .\dist\*
}
else {
    python -m twine upload .\dist\*
}
