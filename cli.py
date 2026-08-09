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

CONFIG_DIR = Path.home() / ".draftbox"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# 模型提供商配置
PROVIDERS = {
    "1": {"name": "Xiaomi MiMo", "key_env": "MIMO_API_KEY", "url": "https://token-plan-cn.xiaomimimo.com/v1", "models": ["mimo-v2.5", "mimo-v2.5-pro", "mimo-v2-omni"]},
    "2": {"name": "DeepSeek", "key_env": "DEEPSEEK_API_KEY", "url": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-coder"]},
    "3": {"name": "OpenAI", "key_env": "OPENAI_API_KEY", "url": "https://api.openai.com/v1", "models": ["gpt-4", "gpt-3.5-turbo"]},
    "4": {"name": "通义千问", "key_env": "DASHSCOPE_API_KEY", "url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "models": ["qwen-turbo", "qwen-plus"]},
    "5": {"name": "智谱AI", "key_env": "ZHIPU_API_KEY", "url": "https://open.bigmodel.cn/api/paas/v4", "models": ["glm-4", "glm-3-turbo"]},
    "6": {"name": "自定义", "key_env": "", "url": "", "models": []},
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
    """模型配置（参考 hermes model）"""
    cfg = load_config()
    current = cfg.get("model", {})

    print(f"""
\x1b[36m  Current model:  {current.get('model', '未配置')}
  Active provider: {current.get('provider', '未配置')}\x1b[0m
""")

    print("  Select provider:")
    for num, p in PROVIDERS.items():
        marker = "●" if current.get("provider") == p["name"] else "○"
        print(f"  ({marker}) {num}. {p['name']}")

    print(f"\n  (○) 0. 返回\n")
    choice = input("  Choice [default 0]: ").strip() or "0"

    if choice == "0":
        return

    if choice not in PROVIDERS:
        print("  ❌ 无效选择")
        return

    provider = PROVIDERS[choice]
    print(f"\n  {provider['name']} API key: ", end="")

    if provider["key_env"]:
        current_key = os.environ.get(provider["key_env"], current.get("api_key", ""))
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
    else:
        current_key = input().strip()

    base_url = input(f"  Base URL [{provider['url']}]: ").strip() or provider["url"]

    # 选择模型
    if provider["models"]:
        print(f"\n  Select default model:")
        for i, m in enumerate(provider["models"], 1):
            marker = "●" if current.get("model") == m else "○"
            print(f"  ({marker}) {i}. {m}")
        print(f"  (○) {len(provider['models'])+1}. Enter custom model name")
        print(f"  (○) {len(provider['models'])+2}. Skip (keep current)\n")

        model_choice = input(f"  Choice [default 1]: ").strip() or "1"
        try:
            idx = int(model_choice) - 1
            if 0 <= idx < len(provider["models"]):
                model_name = provider["models"][idx]
            elif idx == len(provider["models"]):
                model_name = input("  Custom model name: ").strip()
            else:
                model_name = current.get("model", "")
        except:
            model_name = current.get("model", "")
    else:
        model_name = input(f"  Model name [{current.get('model', '')}]: ").strip() or current.get("model", "")

    # 保存配置
    cfg["model"] = {
        "provider": provider["name"],
        "api_key": current_key,
        "base_url": base_url,
        "model": model_name,
    }
    save_config(cfg)

    print(f"\n\x1b[32m  ✅ Default model set to: {model_name} (via {provider['name']})\x1b[0m\n")


def cmd_setup():
    """配置向导"""
    print("""
\x1b[36m╔══════════════════════════════════════════════════════════════╗
║            DraftBox 配置向导                                 ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m
""")
    cfg = load_config()

    print("\x1b[36m  ── 图片搜索 ──\x1b[0m")
    pexels = input(f"  Pexels Key [{cfg.get('search',{}).get('pexels_key','') or '未设置'}]: ").strip()
    if pexels: cfg.setdefault("search",{})["pexels_key"] = pexels

    unsplash = input(f"  Unsplash Key [{cfg.get('search',{}).get('unsplash_key','') or '未设置'}]: ").strip()
    if unsplash: cfg.setdefault("search",{})["unsplash_key"] = unsplash

    print("\n\x1b[36m  ── 服务端口 ──\x1b[0m")
    port = input(f"  后端端口 [{cfg.get('server',{}).get('port',8502)}]: ").strip()
    if port: cfg.setdefault("server",{})["port"] = int(port)

    save_config(cfg)
    print(f"\n\x1b[32m  ✅ 配置完成！\x1b[0m")
    print(f"\n  启动: draftbox start\n")


def cmd_start():
    """启动服务"""
    import subprocess
    ensure_dir()
    cfg = load_config()
    port = cfg.get("server",{}).get("port", 8502)

    print(f"\n🚀 DraftBox 启动中...")
    print(f"   后端: http://localhost:{port}")
    print(f"   前端: http://localhost:3000\n")

    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port), "--host", "0.0.0.0"],
        cwd=str(CONFIG_DIR)
    )

    web_dir = CONFIG_DIR / "web"
    if web_dir.exists():
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
        # 默认启动服务
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
