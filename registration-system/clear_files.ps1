$directories = @(
    "V:\prototype_1_saloon\prototype_1_saloon\registration-system\data\businesses\salon\meta_data",
    "V:\prototype_1_saloon\prototype_1_saloon\registration-system\data\businesses\salon\customer_booking_map",
    "V:\prototype_1_saloon\prototype_1_saloon\registration-system\data\businesses\salon\Customer\live",
    "V:\prototype_1_saloon\prototype_1_saloon\registration-system\data\businesses\salon\Client\live",
    "V:\prototype_1_saloon\prototype_1_saloon\registration-system\data\businesses\salon\ServiceBusinessMap"
)

function DeleteFiles {
    $deletedCount = 0
    $failedCount = 0

    foreach ($path in $directories) {
        $path = $path.Trim()
        
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }
        
        if (Test-Path $path) {
            # If it's a directory, delete all files inside it
            if ((Get-Item $path) -is [System.IO.DirectoryInfo]) {
                $childFiles = Get-ChildItem -Path $path -File -Recurse
                foreach ($file in $childFiles) {
                    try {
                        Remove-Item $file.FullName -Force
                        Write-Host "Deleted: $($file.FullName)" -ForegroundColor Green
                        $deletedCount++
                    } catch {
                        Write-Host "Failed to delete: $($file.FullName) - $_" -ForegroundColor Red
                        $failedCount++
                    }
                }
            } else {
                # If it's a file, delete it directly
                try {
                    Remove-Item $path -Force
                    Write-Host "Deleted: $path" -ForegroundColor Green
                    $deletedCount++
                } catch {
                    Write-Host "Failed to delete: $path - $_" -ForegroundColor Red
                    $failedCount++
                }
            }
        } else {
            Write-Host "Path not found: $path" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`nSummary: $deletedCount deleted, $failedCount failed" -ForegroundColor Cyan
}

function CreateDirectories {
    $createdCount = 0
    $failedCount = 0
    
    foreach ($path in $directories) {
        $path = $path.Trim()
        
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }
        
        if (Test-Path $path) {
            Write-Host "Already exists: $path" -ForegroundColor Yellow
        } else {
            try {
                New-Item -ItemType Directory -Path $path -Force | Out-Null
                Write-Host "Created: $path" -ForegroundColor Green
                $createdCount++
            } catch {
                Write-Host "Failed to create: $path - $_" -ForegroundColor Red
                $failedCount++
            }
        }
    }
    
    Write-Host "`nSummary: $createdCount created, $failedCount failed" -ForegroundColor Cyan
}
# Display menu
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1 - Delete all files in directories" -ForegroundColor Yellow
Write-Host "2 - Create these directories" -ForegroundColor Yellow
Write-Host "3 - Execute a custom command" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
$choice = Read-Host "Enter your choice (1, 2, or 3) [default: 3]"

# # Set default to 3 if no input
# if ([string]::IsNullOrWhiteSpace($choice)) {
#     $choice = "3"
# }

if ($choice -eq "1") {
    DeleteFiles
} elseif ($choice -eq "2") {
    CreateDirectories
} elseif ($choice -eq "3") {
    $command = "python -m uvicorn main:app --reload --no-access-log"
    try {
        Write-Host "Executing: $command" -ForegroundColor Cyan
        Invoke-Expression $command
        Write-Host "Command executed successfully." -ForegroundColor Green
    } catch {
        Write-Host "Error executing command: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Invalid choice. Please enter 1, 2, or 3." -ForegroundColor Red
    exit 1
}
