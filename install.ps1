# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host "🚀 DraftBox 安装中..." -ForegroundColor Cyan

# 安装目录
$InstallDir = "$env:USERPROFILE\.draftbox"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# 下载项目
if (-not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "📥 下载 DraftBox..." -ForegroundColor Yellow
    $url = "https://raw.githubusercontent.com/JCWD123/media_draftbox/master/draftbox_v2.tar.gz"
    $tmpFile = "$env:TEMP\draftbox.tar.gz"
    Invoke-WebRequest -Uri $url -OutFile $tmpFile
    tar -xzf $tmpFile -C $InstallDir
    Remove-Item $tmpFile
}

# 安装 Python 依赖
Write-Host "📦 安装依赖..." -ForegroundColor Yellow
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
try { wewrite --version 2>$null } catch {
    pip install wewrite -q 2>$null
}

# 创建快捷方式
$batContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
python cli.py %*
"@
Set-Content -Path "$env:USERPROFILE\draftbox.cmd" -Value $batContent

# 添加到 PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$env:USERPROFILE*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$env:USERPROFILE", "User")
    Write-Host "✅ 已添加到 PATH（重启终端生效）" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 开始使用:"
Write-Host "   draftbox setup    # 配置向导"
Write-Host ""
