# PowerShell script to test 100 create-customer requests in parallel (10 parallel x 10 iterations)

$baseUrl = "http://localhost:8000"
$endpoint = "$baseUrl/api/v1/makerequest"
$payloadsDir = "payloads"

$success = 0
$failed = 0
$totalRequests = 0

Write-Host "=" * 80
Write-Host "TESTING 100 CREATE-CUSTOMER REQUESTS (10 PARALLEL x 10 ITERATIONS)"
Write-Host "=" * 80

# Get all payload files
$payloadFiles = Get-ChildItem -Path $payloadsDir -Filter "*.json" | Sort-Object Name

Write-Host "`nFound $($payloadFiles.Count) payloads`n"

# Run 10 iterations
for ($iteration = 1; $iteration -le 10; $iteration++) {
    Write-Host "`n--- Iteration $iteration ---"
    
    # Create jobs for parallel execution (10 at a time)
    $jobs = @()
    $requestNum = 1
    
    foreach ($file in $payloadFiles) {
        $payload = Get-Content $file.FullName | ConvertFrom-Json
        
        # Create a background job for each request
        $job = Start-Job -ScriptBlock {
            param($endpoint, $payload, $phone, $reqNum, $iter)
            
            try {
                $response = Invoke-WebRequest -Uri $endpoint -Method Post -ContentType "application/json" -Body (ConvertTo-Json $payload) -TimeoutSec 10 -ErrorAction Stop
                return @{
                    Status = "OK"
                    Phone = $phone
                    RequestNum = $reqNum
                    Iteration = $iter
                }
            }
            catch {
                return @{
                    Status = "FAIL"
                    Phone = $phone
                    RequestNum = $reqNum
                    Iteration = $iter
                    Error = $_.Exception.Message
                }
            }
        } -ArgumentList $endpoint, $payload, $payload.phone, $requestNum, $iteration
        
        $jobs += $job
        $requestNum++
        
        # Wait for jobs to complete if we have 10 running
        if ($jobs.Count -eq 10) {
            $results = $jobs | Wait-Job | Receive-Job
            foreach ($result in $results) {
                if ($result.Status -eq "OK") {
                    $success++
                    Write-Host "[Iter $($result.Iteration)] [Req $($result.RequestNum)] OK $($result.Phone)"
                } else {
                    $failed++
                    Write-Host "[Iter $($result.Iteration)] [Req $($result.RequestNum)] FAIL $($result.Phone)"
                }
                $totalRequests++
            }
            $jobs | Remove-Job
            $jobs = @()
        }
    }
    
    # Wait for remaining jobs
    if ($jobs.Count -gt 0) {
        $results = $jobs | Wait-Job | Receive-Job
        foreach ($result in $results) {
            if ($result.Status -eq "OK") {
                $success++
                Write-Host "[Iter $($result.Iteration)] [Req $($result.RequestNum)] OK $($result.Phone)"
            } else {
                $failed++
                Write-Host "[Iter $($result.Iteration)] [Req $($result.RequestNum)] FAIL $($result.Phone)"
            }
            $totalRequests++
        }
        $jobs | Remove-Job
    }
}

# Print summary
Write-Host "`n" + ("=" * 80)
Write-Host "SUMMARY"
Write-Host "=" * 80
Write-Host "Total: $totalRequests | Success: $success | Failed: $failed"

# Check metadata files
Write-Host "`n" + ("=" * 80)
Write-Host "METADATA CHECK"
Write-Host "=" * 80

$businessMetaPath = "DataModels/Salon/salon_meta.json"
$customerMetaPath = "data/businesses/salon/customer_metadata.json"

if (Test-Path $customerMetaPath) {
    $customerMeta = Get-Content $customerMetaPath | ConvertFrom-Json
    $totalCustomers = $customerMeta.metadata.total_customers
    $customersInCache = $customerMeta.customer.PSObject.Properties.Count
    
    Write-Host "`nBusiness Metadata:"
    Write-Host "  Total Customers: $totalCustomers"
    Write-Host "  Phone Mappings: $(($customerMeta.PSObject.Properties | Where-Object { $_.Name -eq 'phone_mappings' }).Value.PSObject.Properties.Count)"
    
    Write-Host "`nCustomer Metadata:"
    Write-Host "  Customers in Cache: $customersInCache"
    
    # Show first 3 customers
    Write-Host "`nFirst 3 Customers:"
    $count = 0
    foreach ($phone in $customerMeta.customer.PSObject.Properties.Name) {
        if ($count -lt 3) {
            $customer = $customerMeta.customer.$phone
            Write-Host "  Phone: $phone"
            Write-Host "    Customer ID: $($customer.customer_id)"
            Write-Host "    Latest Version: $($customer.latest_latest_version)"
            Write-Host "    Total Versions: $($customer.versions.Count)"
            $count++
        }
    }
}

Write-Host "`nTest completed!"
