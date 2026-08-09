#!/usr/bin/env python3
"""
DraftBox CLI - 交互式配置工具
参考 Hermes 风格的终端配置

用法：
  draftbox              交互式配置
  draftbox config list  查看配置
  draftbox config set   设置配置
  draftbox config get   获取配置
"""
import yaml
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".draftbox"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(cfg):
    ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"✅ 配置已保存: {CONFIG_FILE}")


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


def show_config():
    cfg = load_config()
    if not cfg:
        print("  ⚠️  未配置，运行: draftbox config init")
        return
    print("\n📋 当前配置：")
    print("=" * 50)
    for key, val in flatten(cfg):
        display = str(val)
        if "key" in key.lower() or "secret" in key.lower():
            if val: display = f"{'*' * 8}{str(val)[-4:]}"
        print(f"  {key}: {display}")
    print()


def init_wizard():
    print("""
╔══════════════════════════════════════════════════════════════╗
║            DraftBox 配置向导                                 ║
╚══════════════════════════════════════════════════════════════╝
""")
    cfg = load_config()

    # AI 模型
    print("\x1b[36m  ── AI 模型配置 ──\x1b[0m")
    print("  支持: MiMo / DeepSeek / OpenAI / 本地模型")
    api_key = input(f"  API Key [{cfg.get('model', {}).get('api_key', '') or '未设置'}]: ").strip()
    if api_key:
        cfg.setdefault("model", {})["api_key"] = api_key

    base_url = input(f"  API Base URL [{cfg.get('model', {}).get('base_url', 'https://token-plan-cn.xiaomimimo.com/v1')}]: ").strip()
    if base_url:
        cfg.setdefault("model", {})["base_url"] = base_url

    model_name = input(f"  模型名称 [{cfg.get('model', {}).get('model', 'mimo-v2.5')}]: ").strip()
    if model_name:
        cfg.setdefault("model", {})["model"] = model_name

    # 图片搜索
    print("\n\x1b[36m  ── 图片搜索引擎 ──\x1b[0m")
    print("  支持: Pexels (免费)")
    pexels_key = input(f"  Pexels API Key [{cfg.get('search', {}).get('pexels_key', '') or '未设置'}]: ").strip()
    if pexels_key:
        cfg.setdefault("search", {})["pexels_key"] = pexels_key

    # 服务端口
    print("\n\x1b[36m  ── 服务配置 ──\x1b[0m")
    port = input(f"  后端端口 [{cfg.get('server', {}).get('backend_port', 8502)}]: ").strip()
    if port:
        cfg.setdefault("server", {})["backend_port"] = int(port)

    web_port = input(f"  前端端口 [{cfg.get('server', {}).get('web_port', 3000)}]: ").strip()
    if web_port:
        cfg.setdefault("server", {})["web_port"] = int(web_port)

    save_config(cfg)

    print(f"""
\x1b[32m  ✅ 配置完成！

  配置文件: {CONFIG_FILE}

  启动服务:
    python -m uvicorn backend.main:app --port {cfg.get('server', {}).get('backend_port', 8502)}
    cd web && npm run dev

  访问: http://localhost:{cfg.get('server', {}).get('web_port', 3000)}
\x1b[0m
""")


def interactive():
    print("""
\x1b[36m╔══════════════════════════════════════════════════════════════╗
║            DraftBox 配置管理                                  ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m
""")
    while True:
        try:
            cmd = input("\x1b[36mdraftbox>\x1b[0m ").strip()
            if not cmd: continue
            parts = cmd.split()
            action = parts[0].lower()

            if action in ("quit", "exit", "q"):
                print("  👋 再见！"); break
            elif action == "help":
                print("  config list   查看配置")
                print("  config init   初始化配置向导")
                print("  config set    设置配置")
                print("  config get    获取配置")
                print("  quit          退出")
            elif action == "config":
                if len(parts) > 1 and parts[1] == "init": init_wizard()
                elif len(parts) > 1 and parts[1] == "list": show_config()
                elif len(parts) > 1 and parts[1] == "set" and len(parts) >= 4:
                    cfg = load_config()
                    set_val(cfg, parts[2], " ".join(parts[3:]))
                    save_config(cfg)
                    print(f"  ✅ {parts[2]} = {parts[3]}")
                elif len(parts) > 1 and parts[1] == "get" and len(parts) >= 3:
                    val = get_val(load_config(), parts[2])
                    print(f"  {parts[2]} = {val}" if val else f"  ❌ {parts[2]} 未配置")
                else: print("  用法: config [list|init|set|get]")
            else:
                print(f"  未知命令: {action}，输入 help 查看帮助")
        except (KeyboardInterrupt, EOFError):
            print("\n  👋 再见！"); break
        except Exception as e:
            print(f"  ❌ 错误: {e}")


if __name__ == "__main__":
    ensure_dir()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "config":
            if len(sys.argv) > 2 and sys.argv[2] == "init": init_wizard()
            elif len(sys.argv) > 2 and sys.argv[2] == "list": show_config()
            elif len(sys.argv) > 2 and sys.argv[2] == "set" and len(sys.argv) >= 5:
                cfg = load_config()
                set_val(cfg, sys.argv[3], " ".join(sys.argv[4:]))
                save_config(cfg)
            elif len(sys.argv) > 2 and sys.argv[2] == "get" and len(sys.argv) >= 4:
                val = get_val(load_config(), sys.argv[3])
                print(val if val else "未配置")
        elif cmd == "version": print("DraftBox v1.0.0")
        elif cmd == "help": print("DraftBox CLI - draftbox config init")
        else: interactive()
    else:
        interactive()
