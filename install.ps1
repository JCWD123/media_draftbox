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
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow feedparser -q

# 安装 wewrite
try { wewrite --version 2>$null } catch {
    pip install wewrite -q 2>$null
}

# 安装前端依赖
Write-Host "📦 安装前端依赖..." -ForegroundColor Yellow
$webDir = "$InstallDir\web"
if (Test-Path "$webDir\package.json") {
    Push-Location $webDir
    npm install
    Pop-Location
    Write-Host "  ✅ 前端依赖安装完成" -ForegroundColor Green
}

# 创建 draftbox.cmd（放到 ~/.local/bin/ 优先级更高）
Write-Host "🔧 创建 draftbox 命令..." -ForegroundColor Yellow

$cmdContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
python cli.py %*
"@

# 放到 ~/.local/bin/draftbox.cmd（优先级最高）
$localBin = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $localBin | Out-Null
$cmdPath = "$localBin\draftbox.cmd"
Set-Content -Path $cmdPath -Value $cmdContent -Encoding ASCII
Write-Host "  ✅ 已创建 $cmdPath" -ForegroundColor Green

# 也放到用户目录作为备用
$cmdPathBackup = "$env:USERPROFILE\draftbox.cmd"
Set-Content -Path $cmdPathBackup -Value $cmdContent -Encoding ASCII

# 确保 ~/.local/bin 在用户 PATH 中（永久保存）
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$userProfile = $env:USERPROFILE
$localBinLower = "$userProfile\.local\bin"

if ($currentPath -notlike "*$localBinLower*") {
    Write-Host "🔧 配置环境变量..." -ForegroundColor Yellow
    $newPath = "$currentPath;$localBinLower;$userProfile"
    
    # 使用 setx 永久保存
    if ($newPath.Length -gt 1024) {
        $regPath = "HKCU:\Environment"
        Set-ItemProperty -Path $regPath -Name "Path" -Value $newPath
        Write-Host "  ✅ 已永久添加到用户 PATH（注册表方式）" -ForegroundColor Green
    } else {
        setx PATH "$newPath" | Out-Null
        Write-Host "  ✅ 已永久添加到用户 PATH" -ForegroundColor Green
    }
} else {
    Write-Host "  ✅ ~/.local/bin 已在 PATH 中" -ForegroundColor Green
}

# 更新当前会话 PATH（立即生效）
$env:Path = "$localBin;$userProfile;$env:Path"

Write-Host ""
Write-Host "✅ 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 使用方法（重启终端后永久生效）："
Write-Host "   draftbox setup    # 配置向导"
Write-Host "   draftbox model    # 模型配置"
Write-Host "   draftbox start    # 启动服务"
Write-Host ""

# 立即执行 setup
& "$cmdPath" setup
