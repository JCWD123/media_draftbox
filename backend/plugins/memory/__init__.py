"""
记忆插件 - 参考 hermes-agent 记忆系统
"""
from plugins import Plugin
from typing import Any, Dict, List, Optional
import json
from pathlib import Path
from datetime import datetime


class MemoryPlugin(Plugin):
    """记忆插件 - 持久化存储用户偏好和历史"""

    name = "memory"
    description = "用户记忆系统（偏好、历史、上下文）"
    version = "1.0.0"

    def initialize(self) -> bool:
        """初始化插件"""
        self.memory_dir = Path.home() / ".draftbox" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.preferences_file = self.memory_dir / "preferences.json"
        self.history_file = self.memory_dir / "history.json"
        self._load_memory()
        return True

    def _load_memory(self):
        """加载记忆"""
        self.preferences = self._load_json(self.preferences_file, {})
        self.history = self._load_json(self.history_file, [])

    def _load_json(self, path: Path, default: Any) -> Any:
        """加载 JSON 文件"""
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_json(self, path: Path, data: Any):
        """保存 JSON 文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def execute(self, action: str, **kwargs) -> Any:
        """执行记忆操作"""
        if action == "get_preference":
            return self.get_preference(kwargs.get("key"))
        elif action == "set_preference":
            return self.set_preference(kwargs.get("key"), kwargs.get("value"))
        elif action == "add_history":
            return self.add_history(kwargs.get("content"))
        elif action == "get_history":
            return self.get_history(kwargs.get("limit", 10))
        elif action == "search":
            return self.search(kwargs.get("query"))
        return {"error": f"未知操作: {action}"}

    def get_preference(self, key: str) -> Optional[str]:
        """获取偏好"""
        return self.preferences.get(key)

    def set_preference(self, key: str, value: str) -> bool:
        """设置偏好"""
        self.preferences[key] = value
        self._save_json(self.preferences_file, self.preferences)
        return True

    def add_history(self, content: str) -> bool:
        """添加历史记录"""
        self.history.append({
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        # 只保留最近 100 条
        self.history = self.history[-100:]
        self._save_json(self.history_file, self.history)
        return True

    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取历史记录"""
        return self.history[-limit:]

    def search(self, query: str) -> List[Dict]:
        """搜索历史记录"""
        results = []
        for item in self.history:
            if query.lower() in item.get("content", "").lower():
                results.append(item)
        return results
