# core/case_library.py
"""
案例库

基于文件系统的案例存储和检索
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from .models import Case


class CaseLibrary:
    """案例库（文件系统存储）"""

    def __init__(self, cases_root: str):
        """
        Args:
            cases_root: 案例库根目录
        """
        self.cases_root = Path(cases_root)
        self.cases_root.mkdir(parents=True, exist_ok=True)
        self._index = self._load_index()

    def _load_index(self) -> Dict:
        """加载索引文件"""
        index_file = self.cases_root / "index.json"
        if index_file.exists():
            try:
                with open(index_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"cases": []}

    def _save_index(self) -> None:
        """保存索引文件"""
        index_file = self.cases_root / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def add_case(self, case: Case) -> None:
        """
        添加案例

        Args:
            case: Case 对象
        """
        # 确保分类目录存在
        category_dir = self.cases_root / case.category
        category_dir.mkdir(parents=True, exist_ok=True)

        # 保存案例文件
        case_file = category_dir / f"{case.case_id}.md"
        with open(case_file, "w", encoding="utf-8") as f:
            f.write(self._case_to_md(case))

        # 更新索引
        self._index["cases"].append({
            "case_id": case.case_id,
            "category": case.category,
            "tags": case.tags,
            "outcome": case.outcome,
            "file": str(case_file)
        })
        self._save_index()

    def search_similar(
        self,
        problem: str,
        limit: int = 3,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        搜索相似案例

        Args:
            problem: 问题描述
            limit: 返回数量上限
            category: 限定类别

        Returns:
            相似案例列表（按相似度降序）
        """
        candidates = self._index["cases"]
        if category:
            candidates = [c for c in candidates if c["category"] == category]

        # 计算相似度
        problem_words = set(problem.lower().split())
        scored = []
        for c in candidates:
            case_tags = set(c.get("tags", []))
            # 标签重叠数
            tag_score = len(case_tags & problem_words)
            # 关键词重叠
            keyword_score = len(case_tags & problem_words) * 0.5
            total_score = tag_score + keyword_score
            scored.append((total_score, c))

        # 排序
        scored.sort(key=lambda x: x[0], reverse=True)

        # 取 Top-N
        results = []
        for score, c in scored[:limit]:
            if score > 0:
                case_file = Path(c["file"])
                if case_file.exists():
                    with open(case_file, encoding="utf-8") as f:
                        content = f.read()
                    # 取第一行作为标题
                    lines = content.strip().split("\n")
                    title = lines[0].replace("# 案例：", "").strip() if lines else c["case_id"]
                    results.append({
                        "case_id": c["case_id"],
                        "title": title,
                        "score": round(score, 1),
                        "category": c["category"],
                        "outcome": c.get("outcome", "")
                    })

        return results

    def get_all_categories(self) -> List[str]:
        """获取所有案例类别"""
        categories = set()
        for c in self._index.get("cases", []):
            categories.add(c.get("category", "unknown"))
        return sorted(list(categories))

    def get_stats(self) -> Dict:
        """获取案例库统计"""
        cases = self._index.get("cases", [])
        categories = {}
        outcomes = {}
        for c in cases:
            cat = c.get("category", "unknown")
            outcome = c.get("outcome", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        return {
            "total": len(cases),
            "categories": categories,
            "outcomes": outcomes
        }

    def _case_to_md(self, case: Case) -> str:
        """将 Case 转为 Markdown"""
        return f"""# 案例：{case.problem[:60]}

## 元信息
- **日期**：{case.created_at}
- **类别**：{case.category}
- **标签**：{", ".join(case.tags)}
- **结果**：{case.outcome}

## 问题描述
{case.problem}

## 调研摘要
{case.investigation_summary or "（略）"}

## 诊断结论
{case.diagnosis}

## 执行的方案
{case.plan_executed}

## 结果
{case.result}

## 教训/启发
{case.lessons}
"""
