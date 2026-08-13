# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.ps1 | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 使用 Continue 而非 Stop：安装脚本大量调用外部命令（git/pip/npm/wewrite），
# 这些命令写 stderr 的正常进度/探测输出在 Stop 模式下会被误判为终止错误。
# 关键步骤的成败统一通过 $LASTEXITCODE 显式判断。
$ErrorActionPreference = "Continue"

# 修正控制台编码，避免中文乱码
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # 部分终端不支持，静默忽略
}

Write-Host "🚀 DraftBox 安装中..." -ForegroundColor Cyan

$InstallDir = "$env:USERPROFILE\.draftbox"

# 清理不完整目录（只有不存在 cli.py 时才视为半成品，避免覆盖已安装环境）
if ((Test-Path "$InstallDir") -and -not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "🔄 清理不完整安装..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $InstallDir
}

# 下载项目（sparse-checkout 只取运行必需目录，跳过 docs 下的 16MB 演示视频）
if (-not (Test-Path "$InstallDir\cli.py")) {
    Write-Host "📥 下载 DraftBox..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

    $cloneOk = $false
    $cloneError = $null

    # 优先使用 partial clone + sparse-checkout（git 2.25+，跳过 docs 大文件，速度快）
    # 注意：用 cmd /c 包装 git，避免 PowerShell 把 git 写 stderr 的正常进度输出当作终止错误
    Push-Location $InstallDir
    try {
        cmd /c "git init -q"
        if ($LASTEXITCODE -ne 0) { throw "git init 失败 ($LASTEXITCODE)" }
        cmd /c "git remote add origin https://github.com/JCWD123/media_draftbox.git"
        if ($LASTEXITCODE -ne 0) { throw "git remote add 失败 ($LASTEXITCODE)" }
        cmd /c "git sparse-checkout init --cone"
        cmd /c "git sparse-checkout set cli.py backend web install.ps1 install.sh README.md README.en.md LICENSE VERSION"
        cmd /c "git fetch --depth 1 --filter=blob:none origin main"
        if ($LASTEXITCODE -ne 0) { throw "git fetch 失败 ($LASTEXITCODE)" }
        cmd /c "git checkout FETCH_HEAD"
        if ($LASTEXITCODE -ne 0) { throw "git checkout 失败 ($LASTEXITCODE)" }
        $cloneOk = $true
    } catch {
        $cloneError = $_.Exception.Message
        $cloneOk = $false
    }
    Pop-Location

    # 回退方案：普通 shallow clone（兼容旧 git，不 sparse）
    if (-not $cloneOk) {
        Write-Host "  ⚠️  稀疏检出失败（$cloneError），回退到普通下载..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $InstallDir
        New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
        Push-Location $InstallDir
        try {
            cmd /c "git init -q"
            cmd /c "git remote add origin https://github.com/JCWD123/media_draftbox.git"
            cmd /c "git fetch --depth 1 origin main"
            if ($LASTEXITCODE -ne 0) { throw "git fetch 失败 ($LASTEXITCODE)" }
            cmd /c "git checkout FETCH_HEAD"
            if ($LASTEXITCODE -ne 0) { throw "git checkout 失败 ($LASTEXITCODE)" }
            $cloneOk = $true
        } catch {
            $cloneError = $_.Exception.Message
            $cloneOk = $false
        }
        Pop-Location
    }

    if (-not $cloneOk) {
        Write-Host "❌ 下载失败: $cloneError" -ForegroundColor Red
        Write-Host "   请检查网络连接，或手动克隆到 $InstallDir" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path "$InstallDir\cli.py")) {
        Write-Host "❌ 下载完成但未找到 cli.py，安装中止" -ForegroundColor Red
        exit 1
    }

    Write-Host "  ✅ 项目下载完成" -ForegroundColor Green
} else {
    Write-Host "  ✅ 已存在安装目录，跳过下载" -ForegroundColor Green
}

# 安装 Python 依赖
Write-Host "📦 安装 Python 依赖..." -ForegroundColor Yellow
# 用 cmd /c 包装 pip，避免 pip 写 stderr 在严格模式下被误判终止
# 显式声明 pydantic>=2.0：后端 schemas 用了 field_validator（v2 API），v1 会导致 ImportError 崩溃
cmd /c "pip install fastapi uvicorn pydantic>=2.0 pyyaml requests markdown beautifulsoup4 Pillow feedparser ddgs -q"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  pip 失败，尝试 python -m pip ..." -ForegroundColor Yellow
    cmd /c "python -m pip install fastapi uvicorn pydantic>=2.0 pyyaml requests markdown beautifulsoup4 Pillow feedparser ddgs -q"
}
Write-Host "  ✅ Python 依赖就绪" -ForegroundColor Green

# 安装 wewrite（排版转换依赖，需要 Python >=3.11；缺失时仅影响「排版转换」功能，不阻断安装）
Write-Host "📦 安装 wewrite（排版转换引擎）..." -ForegroundColor Yellow
$wewriteOk = $false
$wewriteCmd = Get-Command wewrite -ErrorAction SilentlyContinue
if ($wewriteCmd) {
    $wewriteOk = $true
    Write-Host "  ✅ wewrite 已安装" -ForegroundColor Green
} else {
    # 先检查 Python 版本，给出精准提示
    $pyVerOut = & python --version 2>&1
    $pyMatch = [regex]::Match("$pyVerOut", 'Python\s+(\d+)\.(\d+)')
    if ($pyMatch.Success) {
        $pyMajor = [int]$pyMatch.Groups[1].Value
        $pyMinor = [int]$pyMatch.Groups[2].Value
        $pyMajorMinor = $pyMajor * 100 + $pyMinor
        $pyVerLabel = "$pyMajor.$pyMinor"
    } else {
        $pyMajorMinor = 0
        $pyVerLabel = "未知"
    }

    if ($pyMajorMinor -lt 311) {
        Write-Host "  ⚠️  当前 Python $pyVerLabel < 3.11，wewrite 需要 Python >=3.11" -ForegroundColor Yellow
        Write-Host "     排版转换功能将不可用；AI 写作/新闻/草稿等核心功能不受影响" -ForegroundColor Yellow
        Write-Host "     如需排版转换，可安装 Python 3.11+ 后运行: pip install wewrite" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠️  wewrite 未安装，尝试自动安装..." -ForegroundColor Yellow
        cmd /c "pip install wewrite -q" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $wewriteOk = $true
            Write-Host "  ✅ wewrite 安装完成" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  wewrite 安装失败（排版转换功能不可用），可稍后手动: pip install wewrite" -ForegroundColor Yellow
        }
    }
}

# ddgs（DuckDuckGo 实时搜索）需要 Python >=3.10；缺失时仅影响「自定义新闻搜索」，不阻断安装
$ddgsCmd = Get-Command ddgs -ErrorAction SilentlyContinue
$hasDdgsModule = $false
if (-not $ddgsCmd) {
    # 用当前 python 探测 import 是否可用
    $ddgsProbe = & python -c "import ddgs" 2>$null
    if ($LASTEXITCODE -eq 0) { $hasDdgsModule = $true }
}
if (($ddgsCmd) -or $hasDdgsModule) {
    Write-Host "📦 ddgs（自定义新闻搜索）已就绪" -ForegroundColor Green
} elseif ($pyMajorMinor -lt 310) {
    Write-Host "  ⚠️  当前 Python $pyVerLabel < 3.10，ddgs 需要 Python >=3.10" -ForegroundColor Yellow
    Write-Host "     自定义新闻搜索（DuckDuckGo）功能将不可用，其余功能不受影响" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠️  ddgs 未安装，可手动: pip install ddgs" -ForegroundColor Yellow
}

# 安装前端依赖
Write-Host "📦 安装前端依赖..." -ForegroundColor Yellow
$webDir = "$InstallDir\web"
if (Test-Path "$webDir\package.json") {
    Push-Location $webDir
    # 使用 cmd /c npm 避免 PowerShell 执行策略问题
    cmd /c "npm install"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠️  前端依赖安装失败（可稍后手动 npm install）" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 前端依赖安装完成" -ForegroundColor Green
    }
    Pop-Location
} else {
    Write-Host "  ⚠️  未找到 web/package.json，跳过前端依赖" -ForegroundColor Yellow
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

# 大小写不敏感判断（Windows PATH 比较需忽略大小写）
$inPath = $false
foreach ($entry in ($currentPath -split ';')) {
    if ($entry -and ($entry -ieq $localBinLower)) {
        $inPath = $true
        break
    }
}

if (-not $inPath) {
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

# 仅在交互式终端时自动进入 setup（避免非交互管道卡住）
# 判断 stdin 是否可交互：irm|iex 管道调用时 stdin 非交互，跳过向导
$isInteractive = $true
try {
    $isInteractive = [Console]::IsInputRedirected -eq $false
} catch {
    $isInteractive = $true
}

if ($isInteractive) {
    Write-Host "🔐 运行配置向导...`n" -ForegroundColor Cyan
    try {
        & "$cmdPath" setup
    } catch {
        Write-Host "  ⚠️  配置向导未能自动运行，请稍后手动执行: draftbox setup" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️  非交互模式，跳过配置向导，请手动执行: draftbox setup" -ForegroundColor Yellow
}
