#!/usr/bin/env python3
"""
DraftBox CLI
用法：
  draftbox           启动服务（默认）
  draftbox setup     配置向导
  draftbox model     模型配置
  draftbox start     启动服务
  draftbox config    配置管理
"""
import yaml
import sys
import os
from pathlib import Path

# tty/termios 只在 Unix 系统可用
if sys.platform != "win32":
    try:
        import tty
        import termios
    except ImportError:
        pass

CONFIG_DIR = Path.home() / ".draftbox"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# 检测是否是交互式终端
def is_interactive():
    return sys.stdin.isatty()

# 安全的 input 函数（非交互模式返回默认值）
def safe_input(prompt, default=""):
    if not is_interactive():
        print(f"{prompt}{default}")
        return default
    return input(prompt).strip() or default

# ... PROVIDERS 和其他配置保持不变 ...

PROVIDERS = [
    ("1",  "Nous Portal", "Everything your agent needs, 300+ models"),
    ("2",  "OpenRouter", "Pay-per-use API aggregator"),
    ("3",  "Mixture of Agents", "Named presets; aggregator acts after reference models"),
    ("4",  "NovitaAI", "Cloud: Model API, Agent Sandbox, GPU Cloud"),
    ("5",  "LM Studio", "Local desktop app with built-in model server"),
    ("6",  "Anthropic", "Claude models via API key or Claude Code"),
    ("7",  "OpenAI ▸", "Codex CLI or direct OpenAI API"),
    ("8",  "Qwen Cloud / DashScope", "Qwen + multi-provider"),
    ("9",  "xAI Grok ▸", "Direct API or SuperGrok / Premium+ OAuth"),
    ("10", "Xiaomi MiMo", "MiMo-V2.5 and V2 models: pro, omni, flash"),
    ("11", "Tencent TokenHub", "Hy3 Preview via tokenhub.tencentmaas.com"),
    ("12", "NVIDIA NIM", "Nemotron models via build.nvidia.com or local NIM"),
    ("13", "GitHub Copilot ▸", "GitHub token API or copilot --acp process"),
    ("14", "Hugging Face Inference Providers", ""),
    ("15", "Google AI Studio", "Native Gemini API"),
    ("16", "Google Vertex AI", "Gemini via GCP; OAuth2 service account or ADC"),
    ("17", "DeepSeek", "V3, R1, coder, direct API"),
    ("18", "Z.AI / GLM", "Zhipu direct API"),
    ("19", "Kimi / Moonshot ▸", "Coding Plan, Moonshot global & China endpoints"),
    ("20", "StepFun Step Plan", "Agent / coding models via Step Plan API"),
    ("21", "MiniMax ▸", "Global, OAuth Coding Plan & China endpoints"),
    ("22", "Ollama Cloud", "Cloud-hosted open models, ollama.com"),
    ("23", "Arcee AI", "Trinity models, direct API"),
    ("24", "GMI Cloud", "Multi-model direct API"),
    ("25", "Kilo Code", "Kilo Gateway API"),
    ("26", "OpenCode ▸", "Zen pay-as-you-go or Go subscription"),
    ("27", "AWS Bedrock", "Claude, Nova, Llama, DeepSeek; IAM or API key"),
    ("28", "Azure Foundry", "OpenAI-style or Anthropic-style endpoint"),
    ("29", "Qwen OAuth", "Reuses local Qwen CLI login"),
    ("30", "Alibaba Cloud Coding Plan", "Dedicated coding tier"),
    ("31", "custom", "direct API"),
    ("32", "Custom endpoint", "enter URL manually"),
    ("33", "Configure auxiliary models...", ""),
    ("34", "Leave unchanged", ""),
]

PROVIDER_MODELS = {
    "1":  ["claude-sonnet-4", "claude-opus-4", "gpt-4o", "deepseek-v3"],
    "2":  ["anthropic/claude-sonnet-4", "openai/gpt-4o", "google/gemini-pro", "deepseek/deepseek-chat"],
    "3":  ["claude-sonnet-4", "gpt-4o", "gemini-pro"],
    "4":  ["deepseek-v3", "llama-3.1-70b"],
    "5":  ["llama-3.1-8b-instruct", "mistral-7b-instruct"],
    "6":  ["claude-sonnet-4", "claude-opus-4", "claude-3.5-haiku"],
    "7":  ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-4o", "o3-mini"],
    "8":  ["qwen3.7-max", "qwen3.7-plus", "qwen3.6-flash"],
    "9":  ["grok-3", "grok-3-mini"],
    "10": ["mimo-v2.5-pro", "mimo-v2.5", "mimo-v2-omni", "mimo-v2-flash"],
    "11": ["hunyuan-turbo"],
    "12": ["nemotron-ultra-253b", "llama-3.3-nemotron-super-49b-v1"],
    "13": ["claude-sonnet-4", "gpt-4o"],
    "14": ["meta-llama/llama-3.1-70b-instruct", "mistralai/mistral-large-latest"],
    "15": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
    "16": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "17": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-r1"],
    "18": ["glm-5", "glm-4-plus", "glm-4-flash"],
    "19": ["moonshot-v1-auto", "kimi-k2"],
    "20": ["step-1-80k", "step-2-16k"],
    "21": ["MiniMax-Text-01", "abab6.5s-chat"],
    "22": ["llama3.1:8b", "mistral:7b"],
    "23": ["trinity-large-preview"],
    "24": ["deepseek-v3", "qwen-72b"],
    "25": ["deepseek-v3", "gpt-4o-mini"],
    "26": ["claude-sonnet-4", "gpt-4o"],
    "27": ["anthropic.claude-sonnet-4-20250514-v1:0", "anthropic.claude-3-5-haiku-20241022-v1:0"],
    "28": ["gpt-4o", "claude-sonnet-4"],
    "29": ["qwen3.7-max", "qwen3.7-plus"],
    "30": ["qwen3.7-max", "qwen3.6-flash"],
}

PROVIDER_URLS = {
    "5":  "http://localhost:1234/v1",
    "10": "https://token-plan-cn.xiaomimimo.com/v1",
    "17": "https://api.deepseek.com/v1",
    "18": "https://open.bigmodel.cn/api/paas/v4",
    "22": "http://localhost:11434/v1",
}


def ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    if not CONFIG_FILE.exists(): return {}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(cfg):
    ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def flatten(d, parent=""):
    items = []
    for k, v in d.items():
        key = f"{parent}.{k}" if parent else k
        if isinstance(v, dict):
            items.extend(flatten(v, key))
        else:
            items.append((key, v))
    return items


def set_val(cfg, path, value):
    keys = path.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    if value.lower() == "true": value = True
    elif value.lower() == "false": value = False
    elif value.isdigit(): value = int(value)
    d[keys[-1]] = value


def get_val(cfg, path):
    for k in path.split("."):
        cfg = cfg.get(k, {})
    return cfg


# ========== 命令实现 ==========

def cmd_model():
    """模型配置"""
    cfg = load_config()
    current = cfg.get("model", {})
    current_provider = current.get("provider", "")
    current_num = current.get("provider_num", "10")

    print(f"""
\x1b[36m  Current model:    {current.get('model', '未配置')}
  Active provider:  {current_provider or '未配置'}\x1b[0m
""")

    print("  Select provider:")
    print("  Select by number, Enter to confirm.\n")

    for num, name, desc in PROVIDERS:
        marker = "●" if num == current_num else "○"
        suffix = f"  ← currently active" if num == current_num else ""
        if desc:
            print(f"  ({marker}) {num:>2}. {name} ({desc}){suffix}")
        else:
            print(f"  ({marker}) {num:>2}. {name}{suffix}")

    print(f"\n  Choice [default {current_num}]: ", end="")
    choice = input().strip() or current_num

    if choice == "34":
        return

    if choice not in [p[0] for p in PROVIDERS]:
        print("  ❌ 无效选择")
        return

    provider_idx = int(choice) - 1
    provider_name = PROVIDERS[provider_idx][1]

    print(f"\n  {provider_name} API key: ", end="")

    current_key = current.get("api_key", "")
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        print(f"{masked} ✓")
        action = input("  [K]eep / [R]eplace / [C]lear (default K): ").strip().upper() or "K"
        if action == "C":
            current_key = ""
        elif action == "R":
            current_key = input("  New API key: ").strip()
    else:
        current_key = input().strip()

    default_url = PROVIDER_URLS.get(choice, "")
    base_url = input(f"\n  Base URL [{default_url}]: ").strip() or default_url

    models = PROVIDER_MODELS.get(choice, [])
    if models:
        print(f"\n  Select default model:")
        print("  Select by number, Enter to confirm.\n")

        for i, m in enumerate(models, 1):
            marker = "●" if m == current.get("model") else "○"
            suffix = f"  ← currently in use" if m == current.get("model") else ""
            print(f"  ({marker}) {i}. {m}{suffix}")

        print(f"  (○) {len(models)+1}. Enter custom model name")
        print(f"  (○) {len(models)+2}. Skip (keep current)\n")

        model_choice = input(f"  Choice [default 1]: ").strip() or "1"
        try:
            idx = int(model_choice) - 1
            if 0 <= idx < len(models):
                model_name = models[idx]
            elif idx == len(models):
                model_name = input("  Custom model name: ").strip()
            else:
                model_name = current.get("model", "")
        except:
            model_name = current.get("model", "")
    else:
        model_name = input(f"  Model name [{current.get('model', '')}]: ").strip() or current.get("model", "")

    cfg["model"] = {
        "provider": provider_name,
        "provider_num": choice,
        "api_key": current_key,
        "base_url": base_url,
        "model": model_name,
    }
    save_config(cfg)

    print(f"\n  Default model set to: {model_name} (via {provider_name})\n")


def cmd_setup():
    """配置向导（支持非交互模式）"""
    print("""
\x1b[36m╔══════════════════════════════════════════════════════════════╗
║            DraftBox 配置向导                                 ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m
""")
    cfg = load_config()

    # 检测是否是交互式终端
    if not is_interactive():
        print("  ⚠️  非交互模式，跳过配置向导")
        print("  请手动编辑配置文件：~/.draftbox/config.yaml")
        print("")
        print("  或者运行：draftbox config set <key> <value>")
        print("")
        return

    # 图片搜索配置
    print("\x1b[36m  ── 图片搜索 ──\x1b[0m")
    
    pexels = safe_input(f"  Pexels Key [{cfg.get('search',{}).get('pexels_key','') or '未设置'}]: ")
    if pexels:
        cfg.setdefault("search",{})["pexels_key"] = pexels
        save_config(cfg)
        print("  ✅ 已保存")

    unsplash = safe_input(f"  Unsplash Key [{cfg.get('search',{}).get('unsplash_key','') or '未设置'}]: ")
    if unsplash:
        cfg.setdefault("search",{})["unsplash_key"] = unsplash
        save_config(cfg)
        print("  ✅ 已保存")

    # 服务端口
    print("\n\x1b[36m  ── 服务端口 ──\x1b[0m")
    port = safe_input(f"  后端端口 [{cfg.get('server',{}).get('port',8502)}]: ")
    if port:
        cfg.setdefault("server",{})["port"] = int(port)
        save_config(cfg)
        print("  ✅ 已保存")

    print(f"\n\x1b[32m  ✅ 配置完成！\x1b[0m")
    print(f"\n  启动: draftbox start\n")


def cmd_start():
    """启动服务"""
    import subprocess
    import shutil
    ensure_dir()
    cfg = load_config()
    port = cfg.get("server",{}).get("port", 8502)

    print(f"\n🚀 DraftBox 启动中...")
    print(f"   后端: http://localhost:{port}")
    print(f"   前端: http://localhost:3000\n")

    # 使用当前运行的 Python 解释器（避免 venv 冲突）
    python_exe = sys.executable
    
    subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.main:app", "--port", str(port), "--host", "0.0.0.0"],
        cwd=str(CONFIG_DIR)
    )

    web_dir = CONFIG_DIR / "web"
    if web_dir.exists():
        # Windows: 使用 cmd /c npm 避免执行策略问题
        if sys.platform == "win32":
            subprocess.Popen(["cmd", "/c", "npm", "run", "dev"], cwd=str(web_dir))
        else:
            subprocess.Popen(["npm", "run", "dev"], cwd=str(web_dir))

    print("✅ 服务已启动！\n")


def cmd_config(args):
    """配置管理"""
    if not args or args[0] == "list":
        cfg = load_config()
        if not cfg:
            print("  ⚠️  未配置，运行: draftbox setup")
            return
        print("\n📋 当前配置：")
        for key, val in flatten(cfg):
            display = str(val)
            if "key" in key.lower() or "secret" in key.lower():
                if val: display = f"{'*' * 8}{str(val)[-4:]}"
            print(f"  {key}: {display}")

    elif args[0] == "set" and len(args) >= 3:
        cfg = load_config()
        set_val(cfg, args[1], " ".join(args[2:]))
        save_config(cfg)
        print(f"  ✅ {args[1]} 已设置")

    elif args[0] == "get" and len(args) >= 2:
        val = get_val(load_config(), args[1])
        print(f"  {args[1]} = {val}" if val else f"  ❌ {args[1]} 未配置")


def main():
    ensure_dir()

    if len(sys.argv) < 2:
        cmd_start()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "setup":
        cmd_setup()
    elif cmd == "model":
        cmd_model()
    elif cmd == "start":
        cmd_start()
    elif cmd == "config":
        cmd_config(args)
    elif cmd == "version":
        print("DraftBox v1.0.0")
    else:
        print(f"  未知命令: {cmd}")


if __name__ == "__main__":
    main()
