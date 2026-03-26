"""
诊断引擎

核心原则：先理解项目是什么，再判断这个项目哪些方面值得优化。

诊断流程：
1. 分析项目类型（网站/API/CLI/数据处理/移动端/桌面端/通用）
2. 每种类型有不同的"好"标准，映射到不同的问题类型优先级
3. 结合用户通过 onboarding 表达的偏好（user_goals + config.yaml priorities）
4. 最后才判断具体问题属于哪个类型，给出加权优先级

不再写死"UX优先"这类逻辑——那个逻辑是通过分析项目类型和用户偏好得出的结论。
"""

from typing import Dict, Any, Optional, List


# -------------------------------------------------------------------
# 项目类型定义
# key: 项目类型ID, label: 人类可读名称
# relevant_types: 该类型项目值得关注的问题类型（顺序表示默认优先级）
# -------------------------------------------------------------------
PROJECT_TYPE_META = {
    "website": {
        "label": "网站/作品集",
        "relevant_types": [
            "visual_design",
            "ux_interaction",
            "performance",
            "seo_discoverability",
            "content",
            "bug_fix",
            "architecture",
            "feature_request",
        ],
        "signals": ["index.html", "src/", "pages/", "components/", "public/"],
        "tech_hints": ["react", "vue", "next", "nuxt", "gatsby", "vite", "webpack", "html", "css"],
    },
    "webapp": {
        "label": "Web 应用（SaaS/CMS/管理后台）",
        "relevant_types": [
            "ux_interaction",
            "performance",
            "visual_design",
            "feature_request",
            "bug_fix",
            "architecture",
            "security",
            "seo_discoverability",
        ],
        "signals": ["src/", "components/", "pages/", "api/", "routes/"],
        "tech_hints": ["react", "vue", "angular", "next", "express", "fastapi", "django"],
    },
    "api_service": {
        "label": "API 服务/后端",
        "relevant_types": [
            "performance",
            "architecture",
            "bug_fix",
            "security",
            "observability",
            "feature_request",
            "scalability",
        ],
        "signals": ["routes/", "endpoints/", "controllers/", "services/", "api/", "server/"],
        "tech_hints": ["express", "fastapi", "django", "flask", "rails", "spring", "grpc", "rest", "api"],
    },
    "cli_tool": {
        "label": "CLI 工具",
        "relevant_types": [
            "usability",
            "performance",
            "error_handling",
            "documentation",
            "feature_request",
            "cross_platform",
        ],
        "signals": ["bin/", "cli/", "commands/", "main.py", "main.go", "__main__.py"],
        "tech_hints": ["python", "go", "rust", "node", "cli", "argparse", "click", "cobra"],
    },
    "data_pipeline": {
        "label": "数据处理/ETL/ML 管道",
        "relevant_types": [
            "performance",
            "accuracy",
            "observability",
            "reliability",
            "feature_request",
            "scalability",
            "documentation",
        ],
        "signals": ["scripts/", "pipeline/", "etl/", "ml/", "training/", "models/"],
        "tech_hints": ["pandas", "numpy", "spark", "airflow", "kafka", "ml", "etl", "pipeline"],
    },
    "mobile_app": {
        "label": "移动端应用",
        "relevant_types": [
            "ux_interaction",
            "performance",
            "visual_design",
            "bug_fix",
            "offline_support",
            "feature_request",
            "architecture",
        ],
        "signals": ["src/", "screens/", "components/", "ios/", "android/"],
        "tech_hints": ["react native", "flutter", "swift", "kotlin", "expo", "capacitor"],
    },
    "desktop_app": {
        "label": "桌面端应用",
        "relevant_types": [
            "ux_interaction",
            "performance",
            "visual_design",
            "bug_fix",
            "cross_platform",
            "feature_request",
        ],
        "signals": ["src/", "components/", "windows/", "mac/", "linux/"],
        "tech_hints": ["electron", "tauri", "qt", "wxwidgets", "pyqt", "pygame"],
    },
    "library_package": {
        "label": "库/包（npm/pypi/gem）",
        "relevant_types": [
            "api_design",
            "documentation",
            "performance",
            "compatibility",
            "feature_request",
            "testing",
        ],
        "signals": ["package.json", "setup.py", "pyproject.toml", "src/", "lib/"],
        "tech_hints": ["npm", "pip", "pypi", "npm registry", "package", "publish"],
    },
    "ai_ml": {
        "label": "AI/ML 项目",
        "relevant_types": [
            "accuracy",
            "performance",
            "observability",
            "data_quality",
            "feature_request",
            "scalability",
            "cost_efficiency",
        ],
        "signals": ["models/", "training/", "inference/", "notebooks/", "ml/", "llm/"],
        "tech_hints": ["openai", "anthropic", "huggingface", "pytorch", "tensorflow", "llm", "model", "rag", "vector"],
    },
    "unknown": {
        "label": "通用/未知类型",
        "relevant_types": [
            "feature_request",
            "performance",
            "bug_fix",
            "documentation",
            "architecture",
        ],
        "signals": [],
        "tech_hints": [],
    },
}

# 问题类型的人类可读标签
DIAG_TYPE_LABELS = {
    "visual_design": "🎨 视觉/美观",
    "ux_interaction": "⚡ 交互体验",
    "performance": "🚀 性能",
    "feature_request": "🆕 功能需求",
    "bug_fix": "🐛 缺陷修复",
    "architecture": "🏗️ 架构",
    "content": "📝 内容/文案",
    "seo_discoverability": "🔍 SEO/可发现性",
    "security": "🔒 安全",
    "observability": "📊 可观测性",
    "usability": "👤 易用性",
    "error_handling": "⚠️ 错误处理",
    "documentation": "📖 文档",
    "accuracy": "🎯 准确性",
    "reliability": "✅ 可靠性",
    "scalability": "📈 扩展性",
    "compatibility": "🔌 兼容性",
    "cross_platform": "🖥️ 跨平台",
    "offline_support": "📴 离线支持",
    "data_quality": "🧹 数据质量",
    "cost_efficiency": "💰 成本效率",
    "api_design": "🔀 API 设计",
    "testing": "🧪 测试",
    "unknown": "❓ 待确认",
}

# 所有问题类型的关键词
DIAG_KEYWORD_MAP = {
    "visual_design": [
        "美观", "视觉", "设计", "配色", "排版", "字体",
        "看起来", "颜值", "风格", "graphic", "design", "visual",
        "color", "layout", "aesthetic", "icon", "动画", "动效"
    ],
    "ux_interaction": [
        "交互", "体验", "流畅", "操作", "按钮", "点击", "hover",
        "效果", "过渡", "smooth", "ux", "interaction", "animation",
        "transition", "micro", "响应", "反馈", "人性化"
    ],
    "performance": [
        "慢", "卡顿", "性能", "加载", "速度", "延迟", "渲染",
        "build", "bundle", "throughput", "latency",
        "slow", "load", "speed", "lag", "优化", "反应慢"
    ],
    "feature_request": [
        "新功能", "需要", "希望", "想要", "增加", "添加", "支持", "实现",
        "feature", "add", "new", "support"
    ],
    "bug_fix": [
        "bug", "错误", "修复", "问题", "异常", "崩溃",
        "不对", "坏了", "失效",
        "fails", "error", "broken", "闪退", "报错"
    ],
    "architecture": [
        "架构", "重构", "设计", "拆解", "解耦", "迁移", "重写", "清理",
        "refactor", "architecture", "coupling", "decouple", "模块化"
    ],
    "content": [
        "文案", "内容", "文字", "描述", "翻译",
        "copy", "content", "text", "description"
    ],
    "seo_discoverability": [
        "seo", "搜索", "排名", "google", "可发现", "索引",
        "search", "ranking", "index", "discover"
    ],
    "security": [
        "安全", "漏洞", "注入", "xss", "csrf", "认证", "授权",
        "security", "vulnerability", "auth", "token"
    ],
    "observability": [
        "监控", "日志", "trace", "指标", "告警", "可观测",
        "monitoring", "logging", "tracing", "metrics", "alert"
    ],
    "usability": [
        "易用", "难用", "方便", "麻烦", "友好", "直观",
        "usability", "usable", "intuitive", "friendly", "ergonomic"
    ],
    "error_handling": [
        "错误处理", "异常处理", "边界", "容错", "graceful",
        "error handling", "exception", "fallback", "resilience"
    ],
    "documentation": [
        "文档", "注释", "readme", "说明",
        "documentation", "docs", "comment", "readme"
    ],
    "accuracy": [
        "准确", "误差", "精度", "幻觉", "偏差",
        "accuracy", "error", "precision", "bias", "hallucination"
    ],
    "reliability": [
        "可靠", "稳定", "故障", "容错", "高可用",
        "reliable", "stable", "failure", "fault tolerant", "ha"
    ],
    "scalability": [
        "扩展", "伸缩", "扩容", "高并发",
        "scale", "scalable", "concurrent", "throughput"
    ],
    "compatibility": [
        "兼容", "适配", "浏览器", "版本",
        "compatible", "compatibility", "browser", "version"
    ],
    "cross_platform": [
        "跨平台", "多平台", "windows", "mac", "linux", "移动端",
        "cross platform", "multi-platform"
    ],
    "offline_support": [
        "离线", "断网", "缓存", "pwa", "service worker",
        "offline", "cache", "pwa"
    ],
    "data_quality": [
        "数据质量", "数据清洗", "脏数据", "缺失",
        "data quality", "cleaning", "preprocessing"
    ],
    "cost_efficiency": [
        "成本", "费用", "省钱", "经济",
        "cost", "expense", "billing", "token"
    ],
    "api_design": [
        "api", "接口", "rest", "graphql", "endpoint",
        "接口设计", "api design", "endpoint"
    ],
    "testing": [
        "测试", "单元测试", "集成测试", "覆盖率",
        "test", "coverage", "unit test", "e2e"
    ],
}


class DiagnoseEngine:
    """诊断引擎"""

    def diagnose(
        self,
        investigation_report: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        诊断入口。

        流程：
        1. 分析项目类型（website/api_service/cli/...）
        2. 扫描项目文件，理解项目结构
        3. 结合用户优先级，计算加权问题类型得分
        4. 生成具体根因分析
        """
        project_context = project_context or {}

        # Step 1: 分析项目类型
        project_type, type_evidence = self._detect_project_type(project_context)

        # Step 2: 获取该类型相关的有效问题类型列表
        relevant_types = PROJECT_TYPE_META.get(project_type, {}).get(
            "relevant_types", ["unknown"]
        )

        # Step 3: 从问题描述 + 调研结果打分
        problem = investigation_report.get("problem", "")
        raw_scores = self._score_all_types(problem, investigation_report)

        # Step 4: 结合项目类型的有效类型过滤
        typed_scores = {
            t: raw_scores.get(t, 0)
            for t in relevant_types
        }

        # Step 5: 结合用户优先级加权（来自 config.yaml priorities）
        priority_weights = self._get_priority_weights(project_context)
        weighted_scores = self._apply_weights(typed_scores, priority_weights)

        # Step 6: 取最高分作为诊断类型
        if max(weighted_scores.values()) == 0:
            top_type = "unknown"
        else:
            top_type = max(weighted_scores, key=weighted_scores.get)

        # Step 7: 根因分析（基于真实调研数据 + 项目类型）
        root_cause = self._analyze_root_cause(
            problem, top_type, investigation_report, project_context,
            project_type, type_evidence
        )

        # Step 8: 优先级
        priority = self._estimate_priority(top_type, problem, priority_weights)

        # Step 9: 置信度
        confidence = self._estimate_confidence(investigation_report)

        # Step 10: 提取具体发现
        findings = self._extract_findings(investigation_report, top_type)

        return {
            "type": top_type,
            "type_label": DIAG_TYPE_LABELS.get(top_type, top_type),
            "project_type": project_type,
            "project_type_label": PROJECT_TYPE_META.get(project_type, {}).get("label", "未知"),
            "type_evidence": type_evidence,
            "root_cause": root_cause,
            "priority": priority,
            "confidence": confidence,
            "findings": findings,
            "relevant_types": relevant_types,
            "typed_scores": typed_scores,
        }

    # ------------------------------------------------------------------
    # 项目类型检测
    # ------------------------------------------------------------------
    def _detect_project_type(self, ctx: Dict[str, Any]) -> tuple:
        """
        分析项目类型。

        信号来源（优先级递减）：
        1. user_goals.md 中的明确描述（最准确）
        2. config.yaml 中的 description
        3. 项目文件结构扫描
        4. 技术栈推断

        Returns:
            (project_type_id, evidence_dict)
        """
        evidence = {}

        # 来源1: user_goals.md
        goals = ctx.get("user_goals", "")
        type_signals_goals = {
            "website": ["个人网站", "作品集", "官网", "landing page", "portfolio site", "个人品牌"],
            "webapp": ["saas", "web应用", "管理后台", "cms", "dashboard", "web app"],
            "api_service": ["api服务", "后端服务", "rest api", "grpc", "bff"],
            "cli_tool": ["cli工具", "命令行工具", "终端工具", "命令行"],
            "data_pipeline": ["数据处理", "etl", "数据管道", "数据清洗", "ml", "机器学习"],
            "mobile_app": ["移动端", "手机应用", "ios", "android", "react native"],
            "desktop_app": ["桌面端", "桌面应用", "electron"],
            "library_package": ["npm包", "pypi包", "sdk", "library", "包"],
            "ai_ml": ["ai工具", "大模型", "llm", "rag", "ai应用", "agent", "智能体"],
        }

        for ptype, keywords in type_signals_goals.items():
            for kw in keywords:
                if kw.lower() in goals.lower():
                    evidence["source"] = "user_goals"
                    evidence["matched_keyword"] = kw
                    return ptype, evidence

        # 来源2: config.yaml description
        config = ctx.get("project_config", {})
        desc = config.get("project", {}).get("description", "") or str(config.get("description", ""))

        for ptype, keywords in type_signals_goals.items():
            for kw in keywords:
                if kw.lower() in desc.lower():
                    evidence["source"] = "config"
                    evidence["matched_keyword"] = kw
                    return ptype, evidence

        # 来源3: 技术栈推断（从 config 或 state）
        tech_stack = ctx.get("tech_stack", {})
        if isinstance(tech_stack, dict):
            ts_str = " ".join(str(v) for v in tech_stack.values()).lower()
        else:
            ts_str = str(tech_stack).lower()

        tech_type_map = {
            "website": ["react", "vue", "next", "nuxt", "gatsby", "html", "css", "vite"],
            "webapp": ["react", "vue", "angular", "next", "express", "fastapi", "django"],
            "api_service": ["express", "fastapi", "django", "flask", "rails", "spring", "grpc"],
            "cli_tool": ["argparse", "click", "cobra", "go", "rust"],
            "data_pipeline": ["pandas", "numpy", "spark", "airflow", "kafka"],
            "mobile_app": ["react native", "flutter", "swift", "kotlin"],
            "desktop_app": ["electron", "tauri", "qt", "pyqt"],
            "library_package": ["npm", "pip", "pypi", "package.json", "setup.py"],
            "ai_ml": ["openai", "anthropic", "huggingface", "pytorch", "tensorflow", "llm", "rag"],
        }

        for ptype, hints in tech_type_map.items():
            for hint in hints:
                if hint in ts_str:
                    evidence["source"] = "tech_stack"
                    evidence["matched_hint"] = hint
                    return ptype, evidence

        # 来源4: 项目路径名推断
        proj_info = ctx.get("project_info", {})
        path_hints = {
            "website": ["website", "site", "landing", "portfolio", "blog", "docs"],
            "cli_tool": ["cli", "cmd", "tool", "bin"],
            "api_service": ["api", "backend", "server", "service"],
            "ai_ml": ["ai", "llm", "rag", "agent", "chatbot", "embedding"],
        }
        name = (proj_info.get("name", "") + " " + proj_info.get("id", "")).lower()
        for ptype, hints in path_hints.items():
            for hint in hints:
                if hint in name:
                    evidence["source"] = "project_name"
                    evidence["matched_hint"] = hint
                    return ptype, evidence

        evidence["source"] = "default"
        return "unknown", evidence

    # ------------------------------------------------------------------
    # 问题类型评分
    # ------------------------------------------------------------------
    def _score_all_types(
        self,
        problem: str,
        report: Dict[str, Any]
    ) -> Dict[str, float]:
        """对所有问题类型打分（0-1），基于关键词匹配 + 调研结果"""
        scores = {}
        problem_lower = problem.lower()

        # 基础分：关键词匹配
        for diag_type, keywords in DIAG_KEYWORD_MAP.items():
            score = sum(0.15 for kw in keywords if kw.lower() in problem_lower)
            scores[diag_type] = min(1.0, score)

        # 加分：调研结果佐证
        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]
        if valid_web:
            for r in valid_web[:3]:
                snippet = (r.get("snippet", "") + " " + r.get("title", "")).lower()
                for diag_type, keywords in DIAG_KEYWORD_MAP.items():
                    if any(kw.lower() in snippet for kw in keywords):
                        scores[diag_type] = min(1.0, scores.get(diag_type, 0) + 0.1)

        # 如果全是0，说明问题描述里没有明确信号，用 unknown
        if max(scores.values()) == 0:
            scores["unknown"] = 0.5

        return scores

    def _get_priority_weights(self, ctx: Dict[str, Any]) -> Dict[str, float]:
        """
        从 config.yaml priorities 读取用户偏好权重。
        用户说"我最在意X" → X对应的问题类型权重 × 2。
        """
        priorities = ctx.get("priorities", [])
        if not priorities:
            return {}

        # dimension 关键词到问题类型的映射
        dim_to_types = {
            "美观": "visual_design",
            "视觉": "visual_design",
            "design": "visual_design",
            "visual": "visual_design",
            "交互": "ux_interaction",
            "体验": "ux_interaction",
            "ux": "ux_interaction",
            "interaction": "ux_interaction",
            "performance": "performance",
            "速度": "performance",
            "性能": "performance",
            "加载": "performance",
            "seo": "seo_discoverability",
            "搜索": "seo_discoverability",
            "可发现": "seo_discoverability",
            "功能": "feature_request",
            "架构": "architecture",
            "安全": "security",
            "监控": "observability",
            "日志": "observability",
            "易用": "usability",
            "文档": "documentation",
            "测试": "testing",
        }

        weights = {}
        for p in priorities:
            dim = p.get("dimension", "")
            weight = float(p.get("weight", 0))
            for kw, dtype in dim_to_types.items():
                if kw.lower() in dim.lower():
                    # 用户说权重0.4 → 该类型得分×1.5
                    weights[dtype] = weights.get(dtype, 1.0) + (weight * 1.5)

        return weights

    def _apply_weights(
        self,
        typed_scores: Dict[str, float],
        priority_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """把用户优先级权重应用到问题类型得分上"""
        result = {}
        for dtype, score in typed_scores.items():
            multiplier = priority_weights.get(dtype, 1.0)
            result[dtype] = score * multiplier

        return result

    # ------------------------------------------------------------------
    # 根因分析
    # ------------------------------------------------------------------
    def _analyze_root_cause(
        self,
        problem: str,
        diag_type: str,
        report: Dict[str, Any],
        ctx: Dict[str, Any],
        project_type: str,
        type_evidence: Dict[str, Any]
    ) -> str:
        """基于项目类型 + 调研数据生成具体的根因分析"""
        lines = []
        type_label = DIAG_TYPE_LABELS.get(diag_type, diag_type)
        proj_label = PROJECT_TYPE_META.get(project_type, {}).get("label", "未知类型")

        lines.append(f"【项目类型】{proj_label}（{type_evidence.get('source', '推断')}）")
        lines.append(f"【问题类型】{type_label}")
        lines.append("")

        # 调研数据
        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]
        cases = report.get("similar_cases", [])

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

        # 根因描述（针对该项目类型 + 问题类型）
        lines.append("【根因分析】")
        root = self._generate_root_cause_text(
            problem, diag_type, project_type, ctx
        )
        lines.append(root)

        return "\n".join(lines).strip()

    def _generate_root_cause_text(
        self,
        problem: str,
        diag_type: str,
        project_type: str,
        ctx: Dict[str, Any]
    ) -> str:
        """根据项目类型和问题类型生成具体的根因描述"""
        problem_snippet = problem[:100]
        tech_stack = ctx.get("tech_stack", {})
        if isinstance(tech_stack, dict):
            ts_str = " ".join(str(v) for v in tech_stack.values())
        else:
            ts_str = str(tech_stack)

        templates = {
            "visual_design": {
                "website": f"用户关注视觉美观，问题描述「{problem_snippet}」指向网站视觉层面。"
                               f"当前技术栈（{ts_str}）具备实现高质量视觉的基础，"
                               f"建议从设计规范建立或现有样式优化入手。",
            },
            "ux_interaction": {
                "website": f"用户关注交互体验，问题「{problem_snippet}」涉及用户操作层面的感受。"
                               f"可参考竞品（Brittany Chiang等）的交互动效设计，"
                               f"评估当前站点的微交互、过渡动画和操作反馈。",
                "webapp": f"问题「{problem_snippet}」聚焦在应用交互体验。"
                             f"建议分析操作流程中的摩擦点，评估是否需要简化操作步骤或增强即时反馈。",
            },
            "performance": {
                "website": f"问题「{problem_snippet}」指向性能/加载速度。"
                               f"建议用 Lighthouse 量化首屏时间和 FCP/LCP。"
                               f"技术栈（{ts_str}）下可针对性做 bundle 分割和资源压缩。",
                "api_service": f"问题「{problem_snippet}」指向 API 性能。"
                                   f"建议分析响应时间分布和吞吐量瓶颈，"
                                   f"评估缓存、连接池、查询优化等方向。",
            },
            "feature_request": f"问题「{problem_snippet}」是功能需求。"
                                   f"建议先明确需求边界和与现有架构的兼容性，再评估开发成本。",
            "bug_fix": f"问题「{problem_snippet}」是缺陷修复。"
                           f"需要先复现问题、定位根因，再确定修复方案。",
            "architecture": f"问题「{problem_snippet}」涉及架构层面。"
                               f"建议先分析当前架构图，评估改动影响面，从小范围变更开始。",
            "content": f"问题「{problem_snippet}」指向内容/文案。"
                           f"建议针对目标受众优化表述，参考同类优质产品的文案风格。",
            "seo_discoverability": f"问题「{problem_snippet}」涉及 SEO/可发现性。"
                                       f"建议用 Lighthouse SEO 审计，分析 meta 标签、结构化数据和内容质量。",
        }

        type_templates = templates.get(diag_type, {})
        if isinstance(type_templates, dict):
            return type_templates.get(project_type, f"问题「{problem_snippet}」属于{DIAG_TYPE_LABELS.get(diag_type, '未知')}类型，需进一步分析。")
        else:
            return type_templates

    # ------------------------------------------------------------------
    # 优先级 & 置信度
    # ------------------------------------------------------------------
    def _estimate_priority(
        self,
        diag_type: str,
        problem: str,
        priority_weights: Dict[str, float]
    ) -> int:
        """结合问题类型 + 用户优先级 + 关键词强度估算优先级"""
        base_priority = {
            "bug_fix": 9, "security": 9,
            "performance": 7, "ux_interaction": 7, "visual_design": 6,
            "usability": 6, "observability": 5, "reliability": 5,
            "architecture": 5, "feature_request": 5,
            "content": 4, "documentation": 4, "seo_discoverability": 4,
            "scalability": 4, "testing": 4,
            "error_handling": 4, "accuracy": 5,
            "compatibility": 3, "cross_platform": 3, "data_quality": 4,
            "cost_efficiency": 3, "offline_support": 3,
            "api_design": 5,
            "unknown": 5,
        }.get(diag_type, 5)

        intensity = sum(
            1 for kw in ["紧急", "重要", "严重", "critical", "urgent", "major"]
            if kw.lower() in problem.lower()
        ) * 2

        weight_boost = 0
        if diag_type in priority_weights:
            weight_boost = int((priority_weights[diag_type] - 1.0) * 3)

        return min(10, max(1, base_priority + intensity + weight_boost))

    def _estimate_confidence(self, report: Dict[str, Any]) -> float:
        """基于调研数据质量估算置信度"""
        cases = report.get("similar_cases", [])
        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]

        if cases and valid_web:
            return 0.9
        elif valid_web:
            return 0.75
        elif cases:
            return 0.7
        return 0.5

    def _extract_findings(
        self,
        report: Dict[str, Any],
        diag_type: str
    ) -> list:
        """从调研结果中提取具体发现"""
        findings = []
        web = report.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]
        for w in valid_web[:5]:
            title = w.get("title", "")
            if title:
                findings.append({"source": "web", "title": title, "snippet": w.get("snippet", "")[:200]})

        cases = report.get("similar_cases", [])
        for c in cases[:3]:
            findings.append({
                "source": "case",
                "category": c.get("category", ""),
                "title": c.get("title", ""),
                "tags": c.get("tags", [])
            })
        return findings
