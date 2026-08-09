#!/usr/bin/env python3
"""
DraftBox CLI
用法：
  draftbox setup     交互式配置向导
  draftbox start     启动服务
  draftbox config    配置管理
"""
import yaml
import sys
import subprocess
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".draftbox"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

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

def cmd_setup():
    """交互式配置向导"""
    print("""
\x1b[36m╔══════════════════════════════════════════════════════════════╗
║            DraftBox 配置向导                                 ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m
""")
    cfg = load_config()

    # AI 模型
    print("\x1b[36m  ── AI 模型 ──\x1b[0m")
    print("  支持: MiMo / DeepSeek / OpenAI")
    key = input(f"  API Key [{cfg.get('model',{}).get('api_key','') or '未设置'}]: ").strip()
    if key: cfg.setdefault("model",{})["api_key"] = key

    url = input(f"  API URL [{cfg.get('model',{}).get('base_url','https://token-plan-cn.xiaomimimo.com/v1')}]: ").strip()
    if url: cfg.setdefault("model",{})["base_url"] = url

    model = input(f"  模型名 [{cfg.get('model',{}).get('model','mimo-v2.5')}]: ").strip()
    if model: cfg.setdefault("model",{})["model"] = model

    # 图片搜索
    print("\n\x1b[36m  ── 图片搜索 ──\x1b[0m")
    pexels = input(f"  Pexels Key [{cfg.get('search',{}).get('pexels_key','') or '未设置'}]: ").strip()
    if pexels: cfg.setdefault("search",{})["pexels_key"] = pexels

    unsplash = input(f"  Unsplash Key [{cfg.get('search',{}).get('unsplash_key','') or '未设置'}]: ").strip()
    if unsplash: cfg.setdefault("search",{})["unsplash_key"] = unsplash

    # 端口
    print("\n\x1b[36m  ── 服务端口 ──\x1b[0m")
    port = input(f"  后端端口 [{cfg.get('server',{}).get('port',8502)}]: ").strip()
    if port: cfg.setdefault("server",{})["port"] = int(port)

    save_config(cfg)
    print(f"\n\x1b[32m  ✅ 配置完成！\x1b[0m")
    print(f"\n  启动: draftbox start\n")


def cmd_start():
    """启动服务"""
    ensure_dir()
    cfg = load_config()
    port = cfg.get("server",{}).get("port", 8502)

    print(f"\n🚀 DraftBox 启动中...")
    print(f"   后端: http://localhost:{port}")
    print(f"   前端: http://localhost:3000\n")

    # 启动后端
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port), "--host", "0.0.0.0"],
        cwd=str(CONFIG_DIR)
    )

    # 启动前端
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
        print("\n\x1b[36mDraftBox - 会学习的AI写作助手\x1b[0m\n")
        print("  draftbox setup   配置向导")
        print("  draftbox start   启动服务")
        print("  draftbox config  查看配置\n")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "setup":
        cmd_setup()
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
