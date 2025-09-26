# PowerShell script to replace Makefile on Windows
param(
    [Parameter(Mandatory=$true)][ValidateSet("verify","demo","audit-pack","logs","release")] [string]$cmd
)

$ErrorActionPreference = "Stop"
python --version | Out-Null
if ($cmd -eq "verify") { python scripts/verify.py; exit 0 }
if ($cmd -eq "demo") { python scripts/demo.py; exit 0 }
if ($cmd -eq "audit-pack") { python scripts/audit_pack.py; exit 0 }
if ($cmd -eq "logs") { python scripts/make_logs.py; exit 0 }
if ($cmd -eq "release") { python scripts/make_release.py; exit 0 }
