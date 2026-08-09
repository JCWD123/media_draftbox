# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host "🚀 DraftBox 安装中..." -ForegroundColor Cyan

# 安装目录
$InstallDir = "$env:USERPROFILE\.draftbox"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

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

# 创建 draftbox.cmd 到用户目录
$cmdContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
python cli.py %*
"@
$cmdPath = "$env:USERPROFILE\draftbox.cmd"
Set-Content -Path $cmdPath -Value $cmdContent -Encoding ASCII

# 添加到用户 PATH（永久生效）
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userProfile = $env:USERPROFILE
if ($userPath -notlike "*$userProfile*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$userProfile", "User")
    Write-Host "✅ 已添加到用户 PATH" -ForegroundColor Green
}

# 更新当前会话 PATH（立即生效）
$env:Path = "$env:Path;$userProfile"

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 立即可用："
Write-Host "   draftbox setup    # 配置向导"
Write-Host ""

# 立即执行 setup
& "$cmdPath" setup
