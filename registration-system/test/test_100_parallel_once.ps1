# PowerShell script to test 100 create-customer requests in parallel (one time only)

$baseUrl = "http://localhost:8000"
$endpoint = "$baseUrl/api/v1/makerequest"
$payloadsDir = "payloads"

$success = 0
$failed = 0
$totalRequests = 0

Write-Host "=" * 80
Write-Host "TESTING 100 CREATE-CUSTOMER REQUESTS IN PARALLEL (ONE TIME ONLY)"
Write-Host "=" * 80

# Get all payload files
$payloadFiles = Get-ChildItem -Path $payloadsDir -Filter "*.json" | Sort-Object Name

Write-Host "`nFound $($payloadFiles.Count) payloads`n"

# Create jobs for all 100 requests in parallel
$jobs = @()

foreach ($file in $payloadFiles) {
    $payload = Get-Content $file.FullName | ConvertFrom-Json
    
    # Create a background job for each request
    $job = Start-Job -ScriptBlock {
        param($endpoint, $payload, $phone, $reqNum)
        
        try {
            $response = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType "application/json" -Body (ConvertTo-Json $payload) -TimeoutSec 10 -ErrorAction Stop
            return @{
                Status = "OK"
                Phone = $phone
                RequestNum = $reqNum
                StatusCode = $response.StatusCode
            }
        }
        catch {
            return @{
                Status = "FAIL"
                Phone = $phone
                RequestNum = $reqNum
                Error = $_.Exception.Message
            }
        }
    } -ArgumentList $endpoint, $payload, $payload.phone, ($payloadFiles.IndexOf($file) + 1)
    
    $jobs += $job
}

Write-Host "Started $($jobs.Count) parallel jobs`n"

# Wait for all jobs to complete
$results = $jobs | Wait-Job | Receive-Job

# Process results
foreach ($result in $results) {
    if ($result.Status -eq "OK") {
        $success++
        Write-Host "[$('{0:000}' -f $result.RequestNum)] OK $($result.Phone)"
    } else {
        $failed++
        Write-Host "[$('{0:000}' -f $result.RequestNum)] FAIL $($result.Phone) - $($result.Error)"
    }
    $totalRequests++
}

# Clean up jobs
$jobs | Remove-Job

# Print summary
Write-Host "`n" + ("=" * 80)
Write-Host "SUMMARY"
Write-Host "=" * 80
Write-Host "Total: $totalRequests | Success: $success | Failed: $failed"
Write-Host "Success Rate: $(($success / $totalRequests * 100).ToString('F2'))%"

# Check metadata files
Write-Host "`n" + ("=" * 80)
Write-Host "METADATA CHECK"
Write-Host "=" * 80

$customerMetaPath = "data/businesses/salon/customer_metadata.json"
$businessMetaPath = "data/businesses/salon/business_meta_data.json"

if (Test-Path $customerMetaPath) {
    $customerMeta = Get-Content $customerMetaPath | ConvertFrom-Json
    $totalCustomers = $customerMeta.metadata.total_customers
    $customersInCache = $customerMeta.customer.PSObject.Properties.Count
    
    Write-Host "`nBusiness Metadata:"
    Write-Host "  Total Customers: $totalCustomers"
    
    Write-Host "`nCustomer Metadata:"
    Write-Host "  Customers in Cache: $customersInCache"
    
    # Show first 5 customers
    Write-Host "`nFirst 5 Customers:"
    $count = 0
    foreach ($phone in $customerMeta.customer.PSObject.Properties.Name) {
        if ($count -lt 5) {
            $customer = $customerMeta.customer.$phone
            Write-Host "  [$($count + 1)] Phone: $phone"
            Write-Host "      Customer ID: $($customer.customer_id)"
            Write-Host "      Latest Version: $($customer.latest_latest_version)"
            Write-Host "      Total Versions: $($customer.versions.Count)"
            $count++
        }
    }
    
    # Show last 5 customers
    Write-Host "`nLast 5 Customers:"
    $allPhones = @($customerMeta.customer.PSObject.Properties.Name)
    $startIdx = [Math]::Max(0, $allPhones.Count - 5)
    $count = 0
    for ($i = $startIdx; $i -lt $allPhones.Count; $i++) {
        $phone = $allPhones[$i]
        $customer = $customerMeta.customer.$phone
        Write-Host "  [$($i + 1)] Phone: $phone"
        Write-Host "      Customer ID: $($customer.customer_id)"
        Write-Host "      Latest Version: $($customer.latest_latest_version)"
        Write-Host "      Total Versions: $($customer.versions.Count)"
    }
}

if (Test-Path $businessMetaPath) {
    $businessMeta = Get-Content $businessMetaPath | ConvertFrom-Json
    $phoneMappings = $businessMeta.phone_mappings.PSObject.Properties.Count
    
    Write-Host "`nBusiness Phone Mappings: $phoneMappings"
}

Write-Host "`nTest completed!"
