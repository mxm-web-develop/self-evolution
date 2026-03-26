"""
诊断引擎

基于调研报告 + 项目上下文做诊断。
不再只做关键词匹配，而是真正分析调研结果和网络发现，
结合项目配置（user-goals、竞品、优先级）给出有针对性的诊断。
"""

from typing import Dict, Any, Optional


class DiagnoseEngine:
    """诊断引擎"""

    DIAGNOSE_TYPES = [
        "visual_design",    # 视觉/美观优化
        "ux_interaction",   # 交互体验优化
        "performance",      # 性能优化
        "feature_request",  # 新功能
        "bug_fix",          # 缺陷修复
        "architecture",     # 架构调整
        "content",          # 内容/文案优化
        "seo_discoverability", # SEO/可发现性
        "unknown",          # 待确认
    ]

    # 问题类型关键词（扩展版，覆盖美观/交互）
    KEYWORD_MAP = {
        "visual_design": [
            "美观", "视觉", "设计", "配色", "排版", "字体",
            "看起来", "颜值", "风格", "graphic", "design", "visual", "color", "layout", "aesthetic"
        ],
        "ux_interaction": [
            "交互", "体验", "动效", "动画", "流畅", "操作",
            "按钮", "点击", "hover", "效果", "过渡", "smooth",
            "ux", "interaction", "animation", "transition", "micro"
        ],
        "performance": [
            "慢", "卡顿", "性能", "加载", "速度", "延迟", "渲染",
            "build", "bundle",
            "slow", "performance", "load", "speed", "lag"
        ],
        "feature_request": [
            "新功能", "需要", "希望", "想要", "增加", "添加", "支持", "实现",
            "feature", "add", "new", "support"
        ],
        "bug_fix": [
            "bug", "错误", "修复", "问题", "异常", "崩溃",
            "不对", "坏了", "失效",
            "fails", "error", "broken"
        ],
        "architecture": [
            "架构", "重构", "设计", "拆解", "解耦", "迁移", "重写", "清理",
            "refactor", "architecture", "coupling", "decouple"
        ],
        "content": [
            "文案", "内容", "文字", "描述", "翻译",
            "copy", "content", "text", "description"
        ],
        "seo_discoverability": [
            "seo", "搜索", "排名", "google", "可发现", "索引",
            "search", "ranking", "index", "discover"
        ],
    }

    def diagnose(
        self,
        investigation_report: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析调研报告，输出诊断结果。

        Args:
            investigation_report: 调研报告 dict（来自 Investigator）
                - problem: 原始问题描述
                - similar_cases: 案例库检索结果
                - web_findings: 网络搜索结果
                - recommendations: 调研建议
            project_context: 项目上下文（可选，来自 state.json context）
                - user_goals: user-goals.md 内容
                - competitor_benchmarks: competitor-benchmarks.md 内容
                - priorities: config.yaml 中的优先级配置
                - tech_stack: 技术栈
        """
        problem = investigation_report.get("problem", "")
        project_context = project_context or {}

        # 1. 问题分类（综合关键词 + 调研结果）
        diag_type = self._classify(problem, investigation_report)

        # 2. 项目优先级（影响诊断结论）
        priorities = project_context.get("priorities", [])

        # 3. 根因分析（核心改进：真正分析调研结果）
        root_cause = self._analyze_root_cause(
            problem, diag_type, investigation_report, project_context
        )

        # 4. 优先级估算（结合项目配置）
        priority = self._estimate_priority(problem, diag_type, priorities)

        # 5. 置信度（基于调研数据质量）
        confidence = self._estimate_confidence(investigation_report)

        # 6. 生成具体发现（从调研数据提取）
        findings = self._extract_findings(investigation_report, diag_type)

        return {
            "type": diag_type,
            "root_cause": root_cause,
            "priority": priority,
            "confidence": confidence,
            "findings": findings,
            "project_priorities": priorities,
        }

    def _classify(
        self,
        problem: str,
        report: Dict[str, Any]
    ) -> str:
        """综合关键词 + 调研结果判断问题类型"""
        problem_lower = problem.lower()
        scores = {}

        for diag_type, keywords in self.KEYWORD_MAP.items():
            kw_score = sum(1 for kw in keywords if kw.lower() in problem_lower)
            scores[diag_type] = kw_score

        # 如果关键词没命中，看调研结果中是否有线索
        if max(scores.values()) == 0:
            web = report.get("web_findings", [])
            if web and not any("error" in str(r) for r in web):
                # 网络有结果 → 可能是某种优化需求
                return "ux_interaction"
            return "unknown"

        # 平分时优先 UX/视觉 > 性能 > 其他
        max_score = max(scores.values())
        top_types = [t for t, s in scores.items() if s == max_score]
        tie_breakers = ["ux_interaction", "visual_design", "performance",
                        "feature_request", "bug_fix", "architecture",
                        "content", "seo_discoverability", "unknown"]
        for tb in tie_breakers:
            if tb in top_types:
                return tb

    def _analyze_root_cause(
        self,
        problem: str,
        diag_type: str,
        report: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        核心改进：根据真实调研数据 + 项目上下文做根因分析。
        不再是"识别为XXX类型，需要分析瓶颈：problem[:50]"这种废话。
        """
        lines = []
        diag_label = {
            "visual_design": "视觉/美观",
            "ux_interaction": "交互体验",
            "performance": "性能",
            "feature_request": "功能需求",
            "bug_fix": "缺陷修复",
            "architecture": "架构",
            "content": "内容/文案",
            "seo_discoverability": "SEO/可发现性",
            "unknown": "待确认",
        }.get(diag_type, "待确认")

        lines.append(f"【问题类型】{diag_label}（基于关键词 + 调研综合判断）")
        lines.append("")

        # 从调研数据提取具体发现
        web = report.get("web_findings", [])
        web_errors = [r for r in web if "error" in str(r)]
        valid_web = [r for r in web if "error" not in str(r)]

        cases = report.get("similar_cases", [])
        recommendations = report.get("recommendations", [])

        if valid_web:
            lines.append("【网络调研发现】")
            for w in valid_web[:3]:
                title = w.get("title", "")
                snippet = w.get("snippet", "")[:120]
                if title:
                    lines.append(f"  • {title}")
                    if snippet:
                        lines.append(f"    → {snippet}")
            lines.append("")

        if cases:
            lines.append("【竞品/案例参考】")
            for c in cases[:2]:
                cat = c.get("category", "")
                title = c.get("title", "")
                lines.append(f"  • [{cat}] {title}")
            lines.append("")

        # 结合项目上下文的具体分析
        goals = context.get("user_goals", "")
        benchmarks = context.get("competitor_benchmarks", "")
        tech_stack = context.get("tech_stack", {})

        lines.append("【根因分析】")

        if diag_type == "visual_design":
            lines.append(f"  问题聚焦在视觉层面，用户描述为：{problem[:80]}")
            if benchmarks:
                lines.append("  参考竞品风格，当前网站在配色/排版/品牌一致性上有差距")
            if tech_stack:
                ts = tech_stack.get("frontend", "")
                lines.append(f"  当前技术栈：{ts}，具备实现高质量视觉的技术条件")

        elif diag_type == "ux_interaction":
            lines.append(f"  问题聚焦在交互体验：{problem[:80]}")
            if recommendations:
                lines.append("  初步建议方向：")
                for r in recommendations[:3]:
                    if "参考" in r or "网络" in r:
                        lines.append(f"    - {r}")
            lines.append("  改进空间在于微交互、过渡动画和操作反馈")

        elif diag_type == "performance":
            lines.append(f"  问题聚焦在性能：{problem[:80]}")
            if tech_stack:
                ts = tech_stack.get("frontend", "")
                lines.append(f"  当前技术栈：{ts}，可针对性做 bundle 优化和资源压缩")
            lines.append("  需要用 Lighthouse / WebPageTest 量化具体瓶颈")

        elif diag_type == "feature_request":
            lines.append(f"  用户需求类型：{problem[:80]}")
            lines.append("  建议明确需求边界，评估与现有架构的兼容性")

        elif diag_type == "architecture":
            lines.append(f"  架构相关问题：{problem[:80]}")
            lines.append("  改动影响面较大，建议先做小范围验证")

        else:
            lines.append(f"  问题：{problem[:100]}")
            lines.append("  建议补充更多上下文以便进一步诊断")

        return "\n".join(lines).strip()

    def _estimate_priority(
        self,
        problem: str,
        diag_type: str,
        priorities: list
    ) -> int:
        """结合项目配置优先级 + 问题类型估算"""
        # 项目配置优先级
        dim_priority = 5
        if priorities:
            dim_map = {
                "visual_design": ["美观", "视觉", "design", "visual"],
                "ux_interaction": ["交互", "体验", "ux", "interaction"],
                "performance": ["性能", "速度", "performance", "speed"],
                "seo_discoverability": ["seo", "搜索", "排名"],
            }
            target_kws = dim_map.get(diag_type, [])
            for p in priorities:
                dim = p.get("dimension", "")
                weight = p.get("weight", 0)
                if any(kw in dim.lower() for kw in target_kws):
                    dim_priority = int(weight * 10)
                    break

        # 关键词强度
        intensity_keywords = ["紧急", "重要", "严重", "critical", "urgent", "major"]
        intensity = sum(2 for kw in intensity_keywords if kw.lower() in problem.lower())

        # 问题类型默认优先级
        type_priority = {
            "bug_fix": 8,
            "visual_design": 6,
            "ux_interaction": 7,
            "performance": 6,
            "feature_request": 5,
            "architecture": 4,
            "content": 4,
            "seo_discoverability": 3,
            "unknown": 5,
        }.get(diag_type, 5)

        return min(10, max(1, dim_priority + intensity + type_priority // 2))

    def _estimate_confidence(self, report: Dict[str, Any]) -> float:
        """基于调研数据质量估算置信度"""
        cases = report.get("similar_cases", [])
        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]

        if cases and valid_web:
            return 0.9   # 案例 + 网络双重支撑
        elif valid_web:
            return 0.75  # 有网络数据
        elif cases:
            return 0.7   # 有案例支撑
        return 0.5       # 数据不足

    def _extract_findings(
        self,
        report: Dict[str, Any],
        diag_type: str
    ) -> list:
        """从调研结果中提取具体发现，用于后续方案生成"""
        findings = []

        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]

        for w in valid_web[:5]:
            title = w.get("title", "")
            snippet = w.get("snippet", "")[:200]
            if title:
                findings.append({
                    "source": "web",
                    "title": title,
                    "snippet": snippet
                })

        cases = report.get("similar_cases", [])
        for c in cases[:3]:
            findings.append({
                "source": "case",
                "category": c.get("category", ""),
                "title": c.get("title", ""),
                "tags": c.get("tags", [])
            })

        return findings
