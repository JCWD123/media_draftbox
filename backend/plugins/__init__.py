"""
插件基类 - 参考 hermes-agent 插件系统
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import importlib


class Plugin(ABC):
    """插件基类"""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enabled = True

    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass

    def cleanup(self):
        """清理资源"""
        pass

    def get_info(self) -> Dict:
        """获取插件信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
        }


class PluginManager:
    """插件管理器 - 参考 hermes-agent 插件系统"""

    def __init__(self, plugins_dir: str = None):
        self.plugins: Dict[str, Plugin] = {}
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent
        self.config_file = self.plugins_dir / "plugins.json"
        self._load_config()

    def _load_config(self):
        """加载插件配置"""
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {"enabled_plugins": [], "plugin_configs": {}}

    def _save_config(self):
        """保存插件配置"""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                plugins.append(item.name)
        return plugins

    def load_plugin(self, name: str) -> Optional[Plugin]:
        """加载插件"""
        if name in self.plugins:
            return self.plugins[name]

        plugin_dir = self.plugins_dir / name
        if not plugin_dir.exists():
            return None

        try:
            module = importlib.import_module(f"plugins.{name}")
            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                config = self.config.get("plugin_configs", {}).get(name, {})
                plugin = plugin_class(config)
                if plugin.initialize():
                    self.plugins[name] = plugin
                    return plugin
        except Exception as e:
            print(f"加载插件 {name} 失败: {e}")

        return None

    def enable_plugin(self, name: str) -> bool:
        """启用插件"""
        if name not in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].append(name)
            self._save_config()
        return True

    def disable_plugin(self, name: str) -> bool:
        """禁用插件"""
        if name in self.config["enabled_plugins"]:
            self.config["enabled_plugins"].remove(name)
            self._save_config()
        return True

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """获取已加载的插件"""
        return self.plugins.get(name)

    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        plugins = []
        for name in self.discover_plugins():
            plugin = self.load_plugin(name)
            if plugin:
                info = plugin.get_info()
                info["enabled"] = name in self.config.get("enabled_plugins", [])
                plugins.append(info)
        return plugins
