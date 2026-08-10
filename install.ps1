# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.ps1 | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ErrorActionPreference = "Stop"

Write-Host "🚀 DraftBox 安装中..." -ForegroundColor Cyan

$InstallDir = "$env:USERPROFILE\.draftbox"

# 清理不完整目录
if ((Test-Path "$InstallDir") -and -not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "🔄 清理旧文件..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $InstallDir
}

# 克隆项目
if (-not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "📥 下载 DraftBox..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Push-Location $InstallDir
    git init -q
    git remote add origin https://github.com/JCWD123/media_draftbox.git
    git fetch --depth 1 origin master -q
    git checkout FETCH_HEAD -q
    Pop-Location
}

# 安装 Python 依赖
Write-Host "📦 安装依赖..." -ForegroundColor Yellow
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
try { wewrite --version 2>$null } catch {
    pip install wewrite -q 2>$null
}

# 创建 draftbox.cmd（永久保存到用户目录）
Write-Host "🔧 创建 draftbox 命令..." -ForegroundColor Yellow

$cmdContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
python cli.py %*
"@
$cmdPath = "$env:USERPROFILE\draftbox.cmd"
Set-Content -Path $cmdPath -Value $cmdContent -Encoding ASCII
Write-Host "  ✅ 已创建 $cmdPath" -ForegroundColor Green

# 添加用户目录到 PATH（永久生效）
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userProfile = $env:USERPROFILE

if ($userPath -notlike "*$userProfile*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$userProfile", "User")
    Write-Host "  ✅ 已添加 $userProfile 到用户 PATH" -ForegroundColor Green
} else {
    Write-Host "  ✅ 用户目录已在 PATH 中" -ForegroundColor Green
}

# 更新当前会话 PATH（立即生效）
$env:Path = "$env:Path;$userProfile"

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 使用方法："
Write-Host "   draftbox setup    # 配置向导"
Write-Host "   draftbox model    # 模型配置"
Write-Host "   draftbox start    # 启动服务"
Write-Host ""

# 立即执行 setup
& "$cmdPath" setup
