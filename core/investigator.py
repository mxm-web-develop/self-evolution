"""动态调研模块：代码扫描 + 大模型/启发式推理 + 外部搜索 + 持续记忆。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from .case_library import CaseLibrary


class Investigator:
    def __init__(self, search_provider, case_library: CaseLibrary):
        self.search_provider = search_provider
        self.case_library = case_library

    def investigate(
        self,
        problem: str,
        project_context: Optional[Dict[str, Any]] = None,
        scanned_code: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        project_context = project_context or {}
        code_scan = scanned_code or self._scan_project_structure(project_context)
        maturity = self._assess_maturity(problem, project_context, code_scan)
        dimensions = self._infer_optimization_dims(problem, project_context, code_scan, maturity)
        queries = self._build_search_queries(problem, project_context, code_scan, maturity, dimensions)
        web_findings = self._web_research(queries)
        similar_cases = self.case_library.search_similar(problem, limit=3)
        findings = self._generate_findings(
            problem=problem,
            project_context=project_context,
            code_scan=code_scan,
            maturity=maturity,
            dimensions=dimensions,
            web_findings=web_findings,
            similar_cases=similar_cases,
        )
        report = {
            "problem": problem,
            "project_snapshot": {
                "project_name": project_context.get("project_info", {}).get("name") or project_context.get("project_id"),
                "project_path": project_context.get("project_path"),
                "user_goals_summary": self._trim(str(project_context.get("user_goals", "")), 500),
                "history_summary": self._history_summary(project_context),
            },
            "scanned_code": code_scan,
            "maturity_assessment": maturity,
            "optimization_dimensions": dimensions,
            "search_queries": queries,
            "similar_cases": similar_cases,
            "web_findings": web_findings,
            "findings": findings,
            "recommendations": [d.get("why_it_matters", "") for d in dimensions[:5] if d.get("why_it_matters")],
        }
        self._debug_print("INVESTIGATION_REPORT", report)
        return report

    def _scan_project_structure(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        project_path = ctx.get("project_path")
        if not project_path:
            project_info = ctx.get("project_info", {})
            path_candidate = project_info.get("path")
            if path_candidate:
                project_path = str(Path(path_candidate).expanduser())
        result = {
            "project_path": project_path,
            "exists": False,
            "top_level_entries": [],
            "key_files": {},
            "signals": [],
            "tech_hints": [],
            "summary": "未找到项目路径，无法直接扫描代码。",
        }
        if not project_path:
            return result

        root = Path(project_path).expanduser()
        if not root.exists() or not root.is_dir():
            result["summary"] = f"项目路径不存在：{root}"
            return result

        result["exists"] = True
        entries = sorted(list(root.iterdir()), key=lambda p: p.name.lower())[:40]
        result["top_level_entries"] = [p.name for p in entries]

        key_candidates = [
            "package.json", "pyproject.toml", "requirements.txt", "README.md", "src", "app", "pages",
            "components", "public", "api", "server", "backend", "frontend", "vite.config.ts",
            "vite.config.js", "next.config.js", "tsconfig.json",
        ]
        for name in key_candidates:
            p = root / name
            if p.exists():
                result["key_files"][name] = "dir" if p.is_dir() else "file"

        if (root / "package.json").exists():
            try:
                pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                dep_keys = list(deps.keys())[:40]
                result["package_name"] = pkg.get("name")
                result["scripts"] = pkg.get("scripts", {})
                result["dependencies"] = dep_keys
                result["tech_hints"].extend(dep_keys)
            except Exception as exc:
                result.setdefault("errors", []).append(f"package.json 解析失败: {exc}")

        readme = root / "README.md"
        if readme.exists():
            try:
                result["readme_excerpt"] = self._trim(readme.read_text(encoding="utf-8"), 1200)
            except Exception:
                pass

        signals = []
        for name in result["top_level_entries"]:
            lowered = name.lower()
            if lowered in {"src", "app", "pages", "components", "public", "api", "server", "backend", "frontend", "models", "scripts"}:
                signals.append(name)
        result["signals"] = signals
        tech_text = " ".join(result.get("dependencies", []) + result.get("top_level_entries", []))
        result["summary"] = f"扫描到 {len(result['top_level_entries'])} 个顶层条目，关键迹象包括：{', '.join(signals[:8]) or '暂无明显结构信号'}。"
        result["inferred_project_shape"] = self._infer_project_shape(tech_text, ctx)
        return result

    def _assess_maturity(self, problem: str, ctx: Dict[str, Any], scan: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        reasons = []
        if scan.get("exists"):
            score += 1
            reasons.append("存在可扫描代码目录")
        if scan.get("readme_excerpt"):
            score += 1
            reasons.append("存在 README/文档")
        if scan.get("dependencies"):
            score += 1
            reasons.append("存在明确依赖与工程化配置")
        if len(scan.get("signals", [])) >= 3:
            score += 1
            reasons.append("项目结构较完整")
        if ctx.get("competitor_benchmarks"):
            score += 1
            reasons.append("已有竞品/标杆输入")
        if ctx.get("priorities"):
            score += 1
            reasons.append("已有明确优化优先级")

        if score <= 2:
            stage = "early"
            label = "早期"
        elif score <= 4:
            stage = "growing"
            label = "成长中"
        else:
            stage = "mature"
            label = "相对成熟"

        standard = self._maturity_standard(scan.get("inferred_project_shape", "general"), stage)
        result = {
            "stage": stage,
            "label": label,
            "score": score,
            "reasoning": reasons,
            "success_signals": standard,
        }
        self._debug_print("MATURITY_ASSESSMENT", result)
        return result

    def _infer_optimization_dims(self, problem: str, ctx: Dict[str, Any], scan: Dict[str, Any], maturity: Dict[str, Any]) -> List[Dict[str, Any]]:
        goals = " ".join([
            problem,
            str(ctx.get("user_goals", "")),
            str(ctx.get("competitor_benchmarks", "")),
            json.dumps(ctx.get("priorities", []), ensure_ascii=False),
            json.dumps(scan.get("dependencies", []), ensure_ascii=False),
        ]).lower()

        candidates = [
            ("品牌表达与定位清晰度", ["品牌", "portfolio", "作品集", "个人品牌", "客户", "合作", "展示"], "成熟项目会让访客迅速理解这个项目是谁、为谁服务、为什么值得信任。"),
            ("视觉系统与一致性", ["视觉", "美观", "设计", "配色", "字体", "插画", "动效"], "成熟项目通常会有统一的视觉语言，而不是局部堆砌效果。"),
            ("交互反馈与浏览流畅度", ["交互", "体验", "动画", "流畅", "scroll", "hover", "transition"], "成熟产品会把动效作为信息传达和引导，而不是单纯炫技。"),
            ("内容结构与转化路径", ["联系方式", "项目经验", "内容", "文案", "cta", "合作"], "成熟项目会把信息层级和行动路径设计得非常清楚。"),
            ("性能与加载质量", ["性能", "加载", "速度", "vite", "bundle", "lazy", "首屏"], "成熟项目的基础体验必须稳定快速，尤其是作品集/品牌站。"),
            ("SEO与可发现性", ["seo", "搜索", "发现", "google", "meta", "sitemap"], "成熟项目会在内容和技术层同时考虑被发现能力。"),
            ("工程可维护性", ["typescript", "架构", "重构", "组件", "可维护", "模块"], "成熟项目除了好看，也要支持持续迭代和低成本演进。"),
        ]

        dims = []
        for name, keywords, why in candidates:
            score = sum(1 for kw in keywords if kw in goals)
            if score > 0:
                dims.append({
                    "dimension": name,
                    "evidence": [kw for kw in keywords if kw in goals][:5],
                    "why_it_matters": why,
                    "priority_hint": min(10, 4 + score),
                })

        if not dims:
            dims.append({
                "dimension": "核心价值表达与成熟度补齐",
                "evidence": ["上下文信号较弱"],
                "why_it_matters": "在信息不足时，先补齐项目定位、成功标准和关键体验链路。",
                "priority_hint": 6,
            })

        dims.sort(key=lambda x: x.get("priority_hint", 0), reverse=True)
        self._debug_print("INFERRED_DIMENSIONS", dims)
        return dims

    def _build_search_queries(self, problem: str, ctx: Dict[str, Any], scan: Dict[str, Any], maturity: Dict[str, Any], dimensions: List[Dict[str, Any]]) -> List[str]:
        shape = scan.get("inferred_project_shape", "general")
        queries = []
        for dim in dimensions[:4]:
            queries.append(f"成熟{shape}项目 {dim['dimension']} 成功标准 最佳实践")
        if problem:
            queries.append(f"{problem} {shape} 最佳实践")
        if maturity.get("stage") == "early":
            queries.append(f"早期{shape}项目 如何快速达到成熟体验标准")
        return queries[:5]

    def _web_research(self, queries: List[str]) -> List[Dict[str, Any]]:
        findings = []
        provider = self.search_provider
        if not provider:
            return findings
        for query in queries:
            try:
                results = provider.search(query, count=3) or []
                for item in results[:3]:
                    findings.append(item.to_dict() if hasattr(item, "to_dict") else dict(item))
            except Exception as exc:
                findings.append({"query": query, "error": str(exc)})
        self._debug_print("WEB_FINDINGS", findings)
        return findings

    def _generate_findings(self, **kwargs) -> List[Dict[str, Any]]:
        maturity = kwargs["maturity"]
        dimensions = kwargs["dimensions"]
        findings = []
        findings.append({
            "title": f"当前项目处于{maturity.get('label', '未知')}阶段",
            "detail": "；".join(maturity.get("reasoning", [])) or "根据项目结构和上下文综合判断",
            "type": "maturity",
        })
        for dim in dimensions[:5]:
            findings.append({
                "title": dim["dimension"],
                "detail": dim.get("why_it_matters", ""),
                "evidence": dim.get("evidence", []),
                "type": "dimension",
            })
        return findings

    def _infer_project_shape(self, text: str, ctx: Dict[str, Any]) -> str:
        joined = f"{text} {ctx.get('user_goals', '')}".lower()
        if any(k in joined for k in ["portfolio", "个人网站", "landing", "vite", "react"]):
            return "作品集/品牌网站"
        if any(k in joined for k in ["api", "backend", "server", "fastapi", "express"]):
            return "后端/API 服务"
        if any(k in joined for k in ["cli", "command", "terminal"]):
            return "CLI 工具"
        if any(k in joined for k in ["agent", "llm", "ai", "rag"]):
            return "AI 应用"
        return "通用软件项目"

    def _maturity_standard(self, shape: str, stage: str) -> List[str]:
        base = {
            "作品集/品牌网站": [
                "访客 5-10 秒内理解定位、能力与合作入口",
                "页面风格统一，关键交互有节奏感但不过载",
                "首屏与核心模块加载快速稳定",
                "项目案例与联系路径清晰可达",
            ],
            "后端/API 服务": [
                "接口边界清晰，错误处理稳定",
                "性能、监控、日志具备基础闭环",
                "关键链路具备可维护性与测试支撑",
            ],
            "AI 应用": [
                "输入输出质量稳定，目标场景清晰",
                "提示词/流程/评估机制可解释",
                "成本、响应速度、异常处理有边界",
            ],
            "通用软件项目": [
                "目标用户和成功标准明确",
                "核心链路可用且可持续迭代",
                "体验、性能、维护性至少有一条清晰基线",
            ],
        }
        return base.get(shape, base["通用软件项目"])

    def _history_summary(self, ctx: Dict[str, Any]) -> str:
        history = ctx.get("analysis_history", "") or ""
        return self._trim(history, 1000)

    def _trim(self, text: str, limit: int) -> str:
        text = text or ""
        return text if len(text) <= limit else text[: limit - 3] + "..."

    def _debug_print(self, label: str, payload: Any) -> None:
        try:
            print(f"\n===== {label} =====")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        except Exception:
            print(f"\n===== {label} =====")
            print(str(payload))
