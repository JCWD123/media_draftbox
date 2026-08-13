# DraftBox Windows 安装脚本
# 用法: irm https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.ps1 | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 使用 Continue 而非 Stop：安装脚本大量调用外部命令（git/pip/npm/uv/wewrite），
# 这些命令写 stderr 的正常进度/探测输出在 Stop 模式下会被误判为终止错误。
# 关键步骤的成败统一通过 $LASTEXITCODE 显式判断。
$ErrorActionPreference = "Continue"

# 关闭 Invoke-WebRequest 进度条（Windows PowerShell 5.1 会因逐字节刷新严重拖慢下载）
$ProgressPreference = "SilentlyContinue"

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

# ============================================================================
# 隔离环境：创建独立的 Python venv（参考 hermes-agent 做法）
# 不污染用户已有的 Anaconda/系统 Python，用 uv 置备项目专属的 Python 3.11，
# 版本墙（ddgs 需 >=3.10、wewrite 需 >=3.11、pydantic 需 v2）在隔离环境里自然满足。
# ============================================================================

$VenvDir = "$InstallDir\venv"
$VenvPython = "$VenvDir\Scripts\python.exe"
# 国内 PyPI 镜像（优先清华，失败回退官方）
$PyIndexUrl = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 定位 uv（系统已有则用，否则尝试通过 pip 临时装一个到用户目录）
function Resolve-Uv {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) { return $uv.Source }

    # 尝试用 pip 装 uv（装到用户 site，仅用于本次置备环境）
    Write-Host "  未检测到 uv，尝试安装..." -ForegroundColor Yellow
    pip install uv -q 2>$null | Out-Null
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) { return $uv.Source }
    return $null
}

$UvExe = Resolve-Uv

# 判断是否需要（重新）创建 venv：不存在，或 python 版本不对
$needVenv = $true
if (Test-Path $VenvPython) {
    $existingVer = & $VenvPython --version 2>&1
    if ($existingVer -match "3\.(1[1-9])") {
        $needVenv = $false
    }
}

if ($needVenv) {
    if (-not $UvExe) {
        Write-Host "❌ 未找到 uv 且无法自动安装（网络受限）" -ForegroundColor Red
        Write-Host "   请手动安装 uv： https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Red
        Write-Host "   或手工创建 venv： python -m venv $VenvDir" -ForegroundColor Red
        exit 1
    }

    Write-Host "🔧 创建隔离环境（Python 3.11）..." -ForegroundColor Cyan
    # 删除旧 venv（若存在且版本不符）
    if (Test-Path $VenvDir) {
        Remove-Item -Recurse -Force $VenvDir
    }

    # uv venv 会输出 "Using CPython ..." 到 stderr，PowerShell 5.1 在 Stop 下会崩溃，
    # 这里已是 Continue 模式，配合 $LASTEXITCODE 判断成败
    & $UvExe venv $VenvDir --python 3.11 2>&1 | Out-Null
    if (-not (Test-Path $VenvPython)) {
        Write-Host "❌ 创建隔离环境失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ 隔离环境就绪" -ForegroundColor Green
} else {
    Write-Host "  ✅ 隔离环境已存在，跳过创建" -ForegroundColor Green
}

# 用 venv 的 python 替换后续所有 python/pip 调用
$script:PyCmd = $VenvPython

# 安装 Python 后端依赖（装进隔离环境，用国内镜像加速）
Write-Host "📦 安装 Python 依赖..." -ForegroundColor Yellow
# 显式声明 pydantic>=2.0：后端 schemas 用了 field_validator（v2 API），v1 会导致 ImportError 崩溃
& $UvExe pip install --python $VenvDir --index-url $PyIndexUrl fastapi uvicorn "pydantic>=2.0" pyyaml requests markdown beautifulsoup4 Pillow feedparser ddgs 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    # 清华镜像失败时，回退官方源
    Write-Host "  ⚠️  镜像源失败，尝试官方源..." -ForegroundColor Yellow
    & $UvExe pip install --python $VenvDir fastapi uvicorn "pydantic>=2.0" pyyaml requests markdown beautifulsoup4 Pillow feedparser ddgs 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Python 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  ✅ Python 依赖就绪" -ForegroundColor Green

# 安装 wewrite（排版转换引擎，Python 3.11 venv 内可正常安装）
Write-Host "📦 安装 wewrite（排版转换引擎）..." -ForegroundColor Yellow
& $UvExe pip install --python $VenvDir --index-url $PyIndexUrl wewrite 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  wewrite 安装失败（排版转换功能将不可用），可稍后手动: draftbox 环境内 pip install wewrite" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ wewrite 就绪" -ForegroundColor Green
}

# 验证关键依赖确实可用（pydantic v2 + ddgs）
$verifyOk = & $VenvPython -c "import pydantic, ddgs; from pydantic import field_validator; print('ok')" 2>&1
if ($verifyOk -notmatch "ok") {
    Write-Host "  ⚠️  依赖验证异常：$verifyOk" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ pydantic v2 + ddgs 验证通过" -ForegroundColor Green
}

# 安装前端依赖
Write-Host "📦 安装前端依赖..." -ForegroundColor Yellow
$webDir = "$InstallDir\web"
if (Test-Path "$webDir\package.json") {
    Push-Location $webDir
    # 前端依赖默认走 npm，可用国内镜像加速
    cmd /c "npm install --registry=https://registry.npmmirror.com"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠️  前端依赖安装失败，回退官方源..." -ForegroundColor Yellow
        cmd /c "npm install"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ⚠️  前端依赖安装失败（可稍后手动 npm install）" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ 前端依赖安装完成" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✅ 前端依赖安装完成" -ForegroundColor Green
    }
    Pop-Location
} else {
    Write-Host "  ⚠️  未找到 web/package.json，跳过前端依赖" -ForegroundColor Yellow
}

# 创建 draftbox.cmd（放到 ~/.local/bin/ 优先级更高）
Write-Host "🔧 创建 draftbox 命令..." -ForegroundColor Yellow

# draftbox.cmd 使用隔离环境的 python.exe（绕开用户系统 Python 的版本墙）
$cmdContent = @"
@echo off
cd /d "%USERPROFILE%\.draftbox"
"%USERPROFILE%\.draftbox\venv\Scripts\python.exe" cli.py %*
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
