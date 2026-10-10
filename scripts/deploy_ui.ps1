# PowerShell script: Build React UI for production and sync to S3 / CloudFront
param (
    [string]$StackName = "regenesis-dev",
    [string]$AwsRegion = "ap-south-1",
    [string]$Profile = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $rootDir "frontend"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  RE:GENESIS - Deploy Web UI to AWS Hosting (S3 / CloudFront)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$extraArgs = @()
if ($Profile -ne "") {
    $extraArgs += @("--profile", $Profile)
}

Write-Host "Querying CloudFormation stack: $StackName (Region: $AwsRegion)..." -ForegroundColor Yellow

try {
    $outputsJson = aws cloudformation describe-stacks `
        --stack-name $StackName `
        --region $AwsRegion `
        --query "Stacks[0].Outputs" `
        --output json @extraArgs | ConvertFrom-Json
} catch {
    Write-Error "Failed to describe stack $StackName. Make sure AWS CLI is authenticated and stack is deployed."
    exit 1
}

$apiUrl = ($outputsJson | Where-Object { $_.OutputKey -eq "ApiUrl" }).OutputValue
$uiBucket = ($outputsJson | Where-Object { $_.OutputKey -eq "UiBucketName" }).OutputValue
$webUrl = ($outputsJson | Where-Object { $_.OutputKey -eq "UiWebsiteUrl" }).OutputValue
$cloudFrontUrl = ($outputsJson | Where-Object { $_.OutputKey -eq "CloudFrontUrl" }).OutputValue
$distId = ($outputsJson | Where-Object { $_.OutputKey -eq "CloudFrontDistributionId" }).OutputValue

if (-not $apiUrl -or -not $uiBucket) {
    Write-Error "Missing ApiUrl or UiBucketName in stack outputs."
    exit 1
}

$apiUrl = $apiUrl.TrimEnd('/')

Write-Host "Stack:           $StackName" -ForegroundColor Green
Write-Host "API Gateway:     $apiUrl" -ForegroundColor Green
Write-Host "Target S3 Bucket: $uiBucket" -ForegroundColor Green
Write-Host "S3 Website URL:  $webUrl" -ForegroundColor Green
if ($cloudFrontUrl) {
    Write-Host "CloudFront URL:  $cloudFrontUrl" -ForegroundColor Green
}

# 1. Build Frontend with Production API URL
Write-Host "`nBuilding Vite frontend bundle..." -ForegroundColor Yellow
Push-Location $frontendDir
try {
    $env:VITE_API_URL = $apiUrl
    npm run build
} finally {
    Pop-Location
}

$distDir = Join-Path $frontendDir "dist"
if (-not (Test-Path $distDir)) {
    Write-Error "Build directory 'dist' was not created."
    exit 1
}

# 2. Sync to S3
Write-Host "`nSyncing assets to s3://$uiBucket/..." -ForegroundColor Yellow
aws s3 sync "$distDir" "s3://$uiBucket/" --delete --region $AwsRegion @extraArgs

# 3. Optional CloudFront invalidation
if ($distId) {
    Write-Host "`nInvalidating CloudFront CDN cache for distribution $distId..." -ForegroundColor Yellow
    try {
        aws cloudfront create-invalidation --distribution-id $distId --paths "/*" @extraArgs
        Write-Host "CloudFront invalidation submitted successfully." -ForegroundColor Green
    } catch {
        Write-Warning "Could not invalidate CloudFront distribution: $_"
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS: RE:GENESIS Web UI Deployed to AWS!" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Primary Live URL: $webUrl" -ForegroundColor Green
if ($cloudFrontUrl) {
    Write-Host "CloudFront CDN:  $cloudFrontUrl" -ForegroundColor Green
}
Write-Host "Connected API:    $apiUrl" -ForegroundColor Green
