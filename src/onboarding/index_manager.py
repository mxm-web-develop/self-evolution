"""
项目索引管理器
维护 projects/index.json，支持列出、查询、设置活跃项目
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class ProjectIndex:
    """项目索引管理器"""

    INDEX_FILE = "projects/index.json"
    SCHEMA_VERSION = "1.0"

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.index_file = self.base_path / self.INDEX_FILE
        self._ensure_index()

    def _ensure_index(self) -> None:
        """确保索引文件存在"""
        if not self.index_file.exists():
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            self._save({
                "schema_version": self.SCHEMA_VERSION,
                "updated_at": self._now(),
                "active_project_id": None,
                "projects": []
            })

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _load(self) -> dict:
        with open(self.index_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        data["updated_at"] = self._now()
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── 查询 ──────────────────────────────────────────

    def list_projects(self) -> List[dict]:
        """列出所有项目"""
        return self._load().get("projects", [])

    def get_project(self, project_id: str) -> Optional[dict]:
        """按 ID 查询项目"""
        for p in self.list_projects():
            if p["id"] == project_id:
                return p
        return None

    def get_active_project(self) -> Optional[dict]:
        """获取当前活跃项目"""
        idx = self._load()
        active_id = idx.get("active_project_id")
        if not active_id:
            return None
        return self.get_project(active_id)

    def get_active_project_id(self) -> Optional[str]:
        return self._load().get("active_project_id")

    def project_exists(self, project_id: str) -> bool:
        """检查项目是否存在"""
        return self.get_project(project_id) is not None

    # ── 修改 ──────────────────────────────────────────

    def add_project(self, project_data: dict) -> None:
        """添加新项目到索引"""
        idx = self._load()
        # 避免重复
        if self.get_project(project_data["id"]):
            raise ValueError(f"Project '{project_data['id']}' already exists")
        idx["projects"].append(project_data)
        # 第一个项目自动设为活跃
        if idx["active_project_id"] is None:
            idx["active_project_id"] = project_data["id"]
        self._save(idx)

    def set_active_project(self, project_id: str) -> None:
        """设置活跃项目"""
        if not self.project_exists(project_id):
            raise ValueError(f"Project '{project_id}' not found")
        idx = self._load()
        idx["active_project_id"] = project_id
        self._save(idx)

    def update_project(self, project_id: str, updates: dict) -> None:
        """更新项目信息（部分更新）"""
        idx = self._load()
        found = False
        for i, p in enumerate(idx["projects"]):
            if p["id"] == project_id:
                idx["projects"][i].update(updates)
                found = True
                break
        if not found:
            raise ValueError(f"Project '{project_id}' not found")
        self._save(idx)

    def remove_project(self, project_id: str) -> None:
        """从索引移除项目（不删除目录）"""
        idx = self._load()
        idx["projects"] = [p for p in idx["projects"] if p["id"] != project_id]
        if idx["active_project_id"] == project_id:
            idx["active_project_id"] = idx["projects"][0]["id"] if idx["projects"] else None
        self._save(idx)

    # ── 工具 ──────────────────────────────────────────

    def make_project_entry(
        self,
        project_id: str,
        name: str,
        project_path: str,
        project_type: str = "new",
        description: str = "",
    ) -> dict:
        """构建标准项目索引条目"""
        now = self._now()
        return {
            "id": project_id,
            "name": name,
            "description": description,
            "path": project_path,
            "type": project_type,  # "new" or "existing"
            "status": "active",
            "created_at": now,
            "last_active_at": now,
            "phase": "IDLE",
            "onboarding_completed": False,
        }

    def to_dict(self) -> dict:
        """返回完整索引数据"""
        return self._load()
