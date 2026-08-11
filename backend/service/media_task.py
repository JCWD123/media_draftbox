"""
媒体后台任务 - 视频生成不阻塞主流程
文字+图片先生成返回，视频任务后台线程执行，前端轮询 media-status
状态持久化到 ~/.draftbox/media/tasks.json（重启不丢失）
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional

MEDIA_DIR = Path.home() / ".draftbox" / "media"
IMAGES_DIR = MEDIA_DIR / "images"
VIDEOS_DIR = MEDIA_DIR / "videos"
COVERS_DIR = MEDIA_DIR / "covers"
TASKS_FILE = MEDIA_DIR / "tasks.json"

for d in (IMAGES_DIR, VIDEOS_DIR, COVERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_tasks: Dict[str, Dict] = {}
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="draftbox-media")


def _load_tasks():
    global _tasks
    if TASKS_FILE.exists():
        try:
            _tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            _tasks = {}


def _save_tasks():
    TASKS_FILE.write_text(json.dumps(_tasks, ensure_ascii=False, indent=1), encoding="utf-8")


def enqueue_video_generation(draft_id: str, video_descs: List[Dict], on_done: Callable = None):
    """
    入队视频生成任务
    video_descs: [{"idx": 1, "prompt": "场景描述"}]
    on_done: 后台线程完成后回调（重渲染 html 等），接收 draft_id
    """
    with _lock:
        _tasks[draft_id] = {
            "status": "running",
            "videos": [],
            "error": "",
            "on_done": None,  # 回调不持久化
        }
        _save_tasks()
    _pool.submit(_worker, draft_id, video_descs, on_done)


def _worker(draft_id: str, video_descs: List[Dict], on_done: Callable):
    from providers import get_video
    import requests as _requests

    try:
        provider = get_video()
        session = _requests.Session()
        session.trust_env = False
        for spec in video_descs:
            result = provider.generate(spec["prompt"], duration=5)
            video_url = result.get("video_url", "")
            cover_url = result.get("cover_url", "")
            idx = spec["idx"]
            mp4_path = VIDEOS_DIR / f"{draft_id}_{idx}.mp4"
            cover_path = COVERS_DIR / f"{draft_id}_{idx}.jpg"
            # 下载 mp4
            resp = session.get(video_url, timeout=120)
            if resp.status_code == 200:
                mp4_path.write_bytes(resp.content)
            # 下载封面（可选）
            if cover_url:
                try:
                    cresp = session.get(cover_url, timeout=60)
                    if cresp.status_code == 200:
                        cover_path.write_bytes(cresp.content)
                except Exception:
                    pass
            with _lock:
                _tasks[draft_id]["videos"].append({
                    "idx": idx,
                    "path": f"/media/videos/{mp4_path.name}",
                    "cover": f"/media/covers/{cover_path.name}" if cover_path.exists() else "",
                    "caption": spec["prompt"][:50],
                })
                _save_tasks()
        with _lock:
            _tasks[draft_id]["status"] = "done"
            _save_tasks()
        if on_done:
            try:
                on_done(draft_id)
            except Exception:
                pass
    except Exception as e:
        with _lock:
            _tasks[draft_id]["status"] = "failed"
            _tasks[draft_id]["error"] = str(e)
            _save_tasks()


def get_video_status(draft_id: str) -> Dict:
    """查询视频任务状态（不含 markdown 大字段）"""
    with _lock:
        task = _tasks.get(draft_id)
        if not task:
            return {"status": "not_found"}
        return {
            "status": task["status"],
            "videos": task.get("videos", []),
            "error": task.get("error", ""),
        }


def get_task_markdown(draft_id: str) -> Optional[str]:
    """获取任务中的 markdown（供 on_done 重渲染）"""
    with _lock:
        task = _tasks.get(draft_id)
        return task.get("markdown") if task else None


def set_task_markdown(draft_id: str, markdown: str):
    with _lock:
        if draft_id in _tasks:
            _tasks[draft_id]["markdown"] = markdown
            _save_tasks()


def set_final_html(draft_id: str, html: str):
    """视频完成后设置最终 HTML（内存态，不持久化；重启后前端重新生成即可）"""
    with _lock:
        if draft_id in _tasks:
            _tasks[draft_id]["final_html"] = html


def get_final_html(draft_id: str) -> Optional[str]:
    with _lock:
        task = _tasks.get(draft_id)
        return task.get("final_html") if task else None


# 启动时加载历史任务
_load_tasks()
