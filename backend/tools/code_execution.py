"""
代码执行工具 - 参考 hermes-agent code_execution_tool.py
支持执行 Python 脚本，带超时和资源限制
"""
import subprocess
import sys
import os
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    duration: float = 0.0
    error: str = ""


class CodeExecutor:
    """代码执行器 - 参考 hermes 架构"""

    def __init__(self, skills_dir: str = None, timeout: int = 30):
        self.skills_dir = Path(skills_dir) if skills_dir else Path(__file__).parent.parent / "skills"
        self.timeout = timeout
        self.max_stdout_bytes = 50_000  # 50KB
        self.max_stderr_bytes = 10_000  # 10KB

    def execute_script(self, script_path: str, args: List[str] = None, **kwargs) -> ExecutionResult:
        """执行 Python 脚本"""
        script = Path(script_path)
        if not script.exists():
            return ExecutionResult(success=False, error=f"脚本不存在: {script_path}")

        cmd = [sys.executable, str(script)] + (args or [])
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(script.parent),
                env={**os.environ, **kwargs.get("env", {})},
            )

            duration = time.time() - start_time
            stdout = result.stdout[:self.max_stdout_bytes]
            stderr = result.stderr[:self.max_stderr_bytes]

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=stdout,
                stderr=stderr,
                returncode=result.returncode,
                duration=duration,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error=f"执行超时（{self.timeout}秒）",
                duration=self.timeout,
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))

    def execute_skill(self, skill_name: str, action: str = "run", args: List[str] = None) -> ExecutionResult:
        """执行 skill"""
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            return ExecutionResult(success=False, error=f"Skill 不存在: {skill_name}")

        # 查找脚本 - 支持多种目录结构
        script = None
        
        # 方式1: scripts/ 目录
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            for pattern in [f"{action}.py", "search.py", "main.py", "*.py"]:
                for f in scripts_dir.glob(pattern):
                    script = f
                    break
            if script:
                return self.execute_script(str(script), args)

        # 方式2: 根目录下的 .py 文件
        for f in skill_dir.glob("*.py"):
            script = f
            break
        if script:
            return self.execute_script(str(script), args)

        # 方式3: 没有脚本，返回 SKILL.md 或 README.md 内容
        for md_name in ["SKILL.md", "README.md"]:
            md_file = skill_dir / md_name
            if md_file.exists():
                content = md_file.read_text(encoding="utf-8")
                return ExecutionResult(success=True, stdout=content)

        return ExecutionResult(success=False, error=f"Skill {skill_name} 没有可执行脚本")

    def execute_code(self, code: str, timeout: int = None) -> ExecutionResult:
        """执行 Python 代码"""
        timeout = timeout or self.timeout

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_script = f.name

        try:
            result = self.execute_script(temp_script, timeout=timeout)
            return result
        finally:
            os.unlink(temp_script)

    def list_skills(self) -> List[Dict]:
        """列出所有可用 skills"""
        skills = []
        if not self.skills_dir.exists():
            return skills

        for item in self.skills_dir.iterdir():
            if item.is_dir():
                # 检查是否有 .py 文件
                has_py = any(item.glob("*.py")) or (item / "scripts" and any((item / "scripts").glob("*.py")))
                has_md = (item / "SKILL.md").exists() or (item / "README.md").exists()
                
                skill_info = {
                    "name": item.name,
                    "has_scripts": has_py,
                    "has_skill_md": has_md,
                }
                skills.append(skill_info)
        return skills


# 全局实例
executor = CodeExecutor()
