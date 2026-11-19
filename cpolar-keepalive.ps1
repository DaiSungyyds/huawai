# cpolar 自动保活脚本
# 每 5 分钟检查隧道状态，断开则自动重启

$cpolarPath = "D:\Cpolar\cpolar.exe"
$port = 5174
$checkInterval = 300  # 5分钟

function Start-Tunnel {
    Write-Host "[$(Get-Date)] Starting cpolar tunnel..."
    Start-Process -FilePath $cpolarPath -ArgumentList "http", $port -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

function Get-TunnelStatus {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

Write-Host "=== cpolar 自动保活脚本 ==="
Write-Host "检查间隔: $checkInterval 秒"
Write-Host "按 Ctrl+C 停止"
Write-Host ""

Start-Tunnel

while ($true) {
    Start-Sleep -Seconds $checkInterval

    $status = Get-TunnelStatus
    if ($status) {
        Write-Host "[$(Get-Date)] Tunnel OK"
    } else {
        Write-Host "[$(Get-Date)] Tunnel DOWN! Restarting..."
        Stop-Process -Name "cpolar" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        Start-Tunnel
    }
}
