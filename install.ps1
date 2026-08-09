# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host "🚀 DraftBox 安装中..." -ForegroundColor Cyan

# 安装目录
$InstallDir = "$env:USERPROFILE\.draftbox"

# 如果目录已存在但不完整，先删除
if ((Test-Path "$InstallDir") -and -not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "🔄 清理旧文件..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $InstallDir
}

# 克隆项目
if (-not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "📥 下载 DraftBox..." -ForegroundColor Yellow
    git clone --depth 1 https://github.com/JCWD123/media_draftbox.git "$InstallDir"
}

# 安装 Python 依赖
Write-Host "📦 安装依赖..." -ForegroundColor Yellow
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
try { wewrite --version 2>$null } catch {
    pip install wewrite -q 2>$null
}

# 创建 draftbox.cmd
$cmdContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
python cli.py %*
"@
$cmdPath = "$env:USERPROFILE\draftbox.cmd"
Set-Content -Path $cmdPath -Value $cmdContent -Encoding ASCII

# 添加到 PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userProfile = $env:USERPROFILE
if ($userPath -notlike "*$userProfile*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$userProfile", "User")
}
$env:Path = "$env:Path;$userProfile"

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""

# 立即执行 setup
& "$cmdPath" setup
