# PowerShell script to test 100 create-customer requests

$baseUrl = "http://localhost:8000"
$endpoint = "$baseUrl/api/v1/makerequest"
$payloadsDir = "payloads"

$success = 0
$failed = 0

Write-Host "=" * 80
Write-Host "TESTING 100 CREATE-CUSTOMER REQUESTS"
Write-Host "=" * 80

# Get all payload files
$payloadFiles = Get-ChildItem -Path $payloadsDir -Filter "*.json" | Sort-Object Name

Write-Host "`nFound $($payloadFiles.Count) payloads`n"

# Send all requests
$i = 1
foreach ($file in $payloadFiles) {
    $payload = Get-Content $file.FullName | ConvertFrom-Json
    
    try {
        $response = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType "application/json" -Body (ConvertTo-Json $payload) -TimeoutSec 10 -ErrorAction Stop
        $success++
        Write-Host "[$('{0:000}' -f $i)] OK $($payload.phone)"
    }
    catch {
        $failed++
        Write-Host "[$('{0:000}' -f $i)] FAIL $($payload.phone)"
    }
    
    $i++
    Start-Sleep -Milliseconds 50
}

# Print summary
Write-Host "`n" + ("=" * 80)
Write-Host "SUMMARY"
Write-Host "=" * 80
Write-Host "Total: $($payloadFiles.Count) | Success: $success | Failed: $failed"

# Check metadata files
Write-Host "`n" + ("=" * 80)
Write-Host "METADATA CHECK"
Write-Host "=" * 80

$businessMetaPath = "DataModels/Salon/salon_meta.json"
$customerMetaPath = "data/businesses/salon/customer_metadata.json"

if (Test-Path $businessMetaPath) {
    $businessMeta = Get-Content $businessMetaPath | ConvertFrom-Json
    Write-Host "`nBusiness Metadata:"
    Write-Host "  Total Customers: $($businessMeta.metadata.total_customers)"
    Write-Host "  Phone Mappings: $($businessMeta.phone_mappings.PSObject.Properties.Count)"
}

if (Test-Path $customerMetaPath) {
    $customerMeta = Get-Content $customerMetaPath | ConvertFrom-Json
    Write-Host "`nCustomer Metadata:"
    Write-Host "  Customers in Cache: $($customerMeta.customers.PSObject.Properties.Count)"
}

Write-Host "`nTest completed!"
