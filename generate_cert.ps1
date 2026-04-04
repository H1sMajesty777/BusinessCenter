# generate_cert.ps1
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "SSL CERTIFICATE GENERATOR FOR LOCALHOST" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Create certs directory
$certsDir = "c:/Vs Code/BusinessCenter/nginx/ssl"
New-Item -ItemType Directory -Force -Path $certsDir | Out-Null

Write-Host "`n[1/4] Creating directory: $certsDir" -ForegroundColor Yellow

# Check OpenSSL
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $opensslPath) {
    Write-Host "`n[ERROR] OpenSSL not found!" -ForegroundColor Red
    Write-Host "Please install OpenSSL:" -ForegroundColor Yellow
    Write-Host "  Windows: choco install openssl" -ForegroundColor White
    Write-Host "  Or download: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor White
    exit 1
}

Write-Host "[2/4] Generating private key and certificate..." -ForegroundColor Yellow

# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes `
    -keyout "$certsDir/key.pem" `
    -out "$certsDir/cert.pem" `
    -days 365 `
    -subj "/C=RU/ST=Moscow/L=Moscow/O=BusinessCenter/CN=localhost"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to generate certificate" -ForegroundColor Red
    exit 1
}

Write-Host "[3/4] Generating DH parameters (may take a minute)..." -ForegroundColor Yellow
openssl dhparam -out "$certsDir/dhparam.pem" 2048

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "SUCCESS! Certificates created in:" -ForegroundColor Green
Write-Host "  $certsDir" -ForegroundColor White
Write-Host "`nFiles:" -ForegroundColor Yellow
Write-Host "  - cert.pem     (certificate)" -ForegroundColor Gray
Write-Host "  - key.pem      (private key)" -ForegroundColor Gray
Write-Host "  - dhparam.pem  (DH parameters)" -ForegroundColor Gray

Write-Host "`n" + "="*60 -ForegroundColor Yellow
Write-Host "NOTE: Browser will show a warning - this is normal" -ForegroundColor Yellow
Write-Host "Click 'Proceed to localhost' to continue" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Yellow