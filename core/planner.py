"""
方案生成模块

根据诊断结果 + 项目上下文 + 调研数据生成量身定制的候选方案。
不再使用硬编码的"渐进式/全面重构/折中"模板，
而是根据问题类型、技术栈、竞品参考生成具体的方案。
"""

from typing import Dict, List, Any, Optional
from .models import Plan
import uuid


class Planner:
    """方案生成模块"""

    # 不同问题类型对应的具体改进方向（不再空泛）
    IMPROVEMENT_DIRECTIONS = {
        "visual_design": [
            {
                "title": "视觉风格统一化",
                "description": "统一配色系统、品牌图形、字体层级，建立设计规范（Design Token）",
                "scope": "局部（样式层）",
                "effort": "低",
                "impact": "立即提升品牌感知",
                "actions": ["建立CSS变量系统", "统一插画风格", "优化字体加载"]
            },
            {
                "title": "全新视觉语言重构",
                "description": "基于竞品分析，引入更现代的视觉风格（暗色/渐变/几何图形）",
                "scope": "全局（设计+实现）",
                "effort": "高",
                "impact": "彻底改变网站视觉印象",
                "actions": ["重新设计组件库", "引入动效设计", "品牌图形升级"]
            },
        ],
        "ux_interaction": [
            {
                "title": "微交互增强",
                "description": "为关键交互点（按钮、卡片、表单）添加 hover/active/transition 效果",
                "scope": "局部（组件层）",
                "effort": "低",
                "impact": "显著提升操作反馈感",
                "actions": ["按钮状态动效", "卡片hover效果", "页面过渡动画"]
            },
            {
                "title": "滚动交互系统",
                "description": "接入 IntersectionObserver/ScrollTrigger，实现元素进入视口时的动画",
                "scope": "局部（交互动效）",
                "effort": "中",
                "impact": "现代感大幅提升",
                "actions": ["滚动触发动画", "stagger动画编排", "导航active状态"]
            },
            {
                "title": "交互体验全面重构",
                "description": "重新设计交互模式，参考标杆案例的交互动效和操作流程",
                "scope": "全局（UX+实现）",
                "effort": "高",
                "impact": "交互体验质的飞跃",
                "actions": ["竞品交互分析", "交互原型设计", "全站动效实现"]
            },
        ],
        "performance": [
            {
                "title": "按需加载优化",
                "description": "路由级代码分割 + 图片懒加载 + 字体子集化",
                "scope": "局部（性能）",
                "effort": "低",
                "impact": "首屏加载速度提升30-50%",
                "actions": ["React.lazy路由分割", "图片懒加载", "字体优化"]
            },
            {
                "title": "性能深度优化",
                "description": "Bundle分析、CSS-in-JS替换、CDN加速、缓存策略",
                "scope": "全局（架构层）",
                "effort": "中",
                "impact": "全面提升加载和运行性能",
                "actions": ["Vite bundle分析", "CDN接入", "HTTP缓存头"]
            },
        ],
        "content": [
            {
                "title": "文案优化",
                "description": "精简Hero区描述，更精准传达AI工具开发者身份",
                "scope": "局部（内容层）",
                "effort": "低",
                "impact": "访客第一眼就能理解你是谁",
                "actions": ["Hero文案重构", "About段落精简", "项目描述优化"]
            },
        ],
        "feature_request": [
            {
                "title": "MVP方案实现",
                "description": "先做最小可行版本，上线验证后再迭代",
                "scope": "局部",
                "effort": "中",
                "impact": "快速验证需求价值",
                "actions": ["需求边界确认", "MVP设计", "核心功能实现"]
            },
        ],
        "architecture": [
            {
                "title": "渐进式重构",
                "description": "按模块逐步重构，优先处理耦合最高的部分",
                "scope": "全局",
                "effort": "高",
                "impact": "长期可维护性提升",
                "actions": ["依赖分析", "模块拆分", "接口规范化"]
            },
        ],
        "seo_discoverability": [
            {
                "title": "基础SEO优化",
                "description": "Meta标签、结构化数据、sitemap、OG图片",
                "scope": "局部",
                "effort": "低",
                "impact": "搜索引擎收录改善",
                "actions": ["Meta标签完善", "JSON-LD结构化数据", "og-image优化"]
            },
        ],
        "unknown": [
            {
                "title": "调研后再定方案",
                "description": "补充更多上下文信息后再生成具体方案",
                "scope": "待定",
                "effort": "低",
                "impact": "待评估",
                "actions": ["补充项目背景", "明确优化目标", "界定成功标准"]
            },
        ],
    }

    def generate_plans(
        self,
        problem: str,
        diagnosis: Dict[str, Any],
        investigation: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[Plan]:
        """
        根据诊断结果 + 项目上下文生成量身定制的方案。

        Args:
            problem: 原始问题描述
            diagnosis: 诊断结果（含 type, findings, project_priorities）
            investigation: 调研报告（含 web_findings, similar_cases ）
            project_context: 项目配置上下文（可选）
        """
        diag_type = diagnosis.get("type", "unknown")
        project_context = project_context or {}
        tech_stack = project_context.get("tech_stack", {})

        # 获取针对该问题类型的具体方案方向
        directions = self.IMPROVEMENT_DIRECTIONS.get(diag_type, [])

        if not directions:
            # fallback：通用三档
            return self._generate_generic_plans(problem, diag_type)

        plans = []

        for i, direction in enumerate(directions):
            plan = self._build_plan(
                direction=direction,
                problem=problem,
                diag_type=diag_type,
                diagnosis=diagnosis,
                investigation=investigation,
                tech_stack=tech_stack,
                index=i
            )
            plans.append(plan)

        # 始终生成一个"低投入快速改进" + 一个"高投入深度改进"
        # 如果 directions 只有1个，补充一个快速方案
        if len(plans) == 1:
            quick = self._build_quick_win(problem, diag_type, tech_stack)
            plans.insert(0, quick)

        # 限制最多3个方案
        return plans[:3]

    def _build_plan(
        self,
        direction: Dict[str, Any],
        problem: str,
        diag_type: str,
        diagnosis: Dict[str, Any],
        investigation: Dict[str, Any],
        tech_stack: Dict[str, Any],
        index: int
    ) -> Plan:
        """根据方向构建一个具体方案"""
        actions = direction.get("actions", [])
        scope = direction.get("scope", "")
        effort = direction.get("effort", "中")

        # 生成具体的行动项（来自调研数据）
        action_items = self._generate_action_items(
            actions, diag_type, investigation, tech_stack
        )

        # 生成预期成果（具体可衡量）
        expected = self._generate_expected_outcomes(
            direction, diag_type, investigation
        )

        # 生成风险（具体，不是模板）
        risks = self._generate_risks(direction, diag_type)

        effort_map = {"低": 1, "中": 2, "高": 3}
        effort_score = effort_map.get(effort, 2)

        return Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title=direction.get("title", "优化方案"),
            description=(
                f"【{scope} · {effort}投入】{direction.get('description', '')}\n"
                f"问题：{problem[:80]}"
            ),
            pros=self._generate_pros(direction, diag_type, investigation),
            cons=self._generate_cons(direction, diag_type),
            resource_estimate={
                "effort": effort,
                "scope": scope,
                "automation": "高" if effort == "低" else ("中" if effort == "中" else "低"),
                "execution_style": "小步快跑" if effort == "低" else ("阶段推进" if effort == "高" else "迭代式")
            },
            risks=risks,
            expected_outcomes=expected,
            action_items=action_items,  # 新增：具体行动项
            scores=None,
            approved=None,
            approver_notes=None
        )

    def _generate_action_items(
        self,
        base_actions: List[str],
        diag_type: str,
        investigation: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> List[str]:
        """基于调研数据和项目技术栈，生成具体的行动项"""
        items = []

        # 加入从调研数据提取的具体参考
        findings = investigation.get("web_findings", [])
        valid_findings = [f for f in findings if "error" not in str(f)]

        # 技术栈适配
        ts = tech_stack.get("frontend", "")
        ts_lower = ts.lower()

        # 基于技术的具体行动
        if "react" in ts_lower:
            if "scroll" in str(base_actions).lower():
                items.append("接入 react-intersection-observer 或 framer-motion 的 Scroll")
            if "lazy" in str(base_actions).lower() or "分割" in str(base_actions).lower():
                items.append("使用 React.lazy + Suspense 做路由级代码分割")
            if "css" in str(base_actions).lower() or "变量" in str(base_actions).lower():
                items.append("在 src/styles/ 下建立 CSS 变量（Design Token）系统")

        if "vite" in ts_lower:
            items.append("运行 vite build --mode production 后分析 bundle 体积")

        if "typescript" in ts_lower:
            items.append("确保新增组件有完整的 TypeScript 类型定义")

        # 竞品参考的具体借鉴
        cases = investigation.get("similar_cases", [])
        for case in cases[:1]:
            cat = case.get("category", "")
            title = case.get("title", "")
            if title:
                items.append(f"参考案例「{title}」的{cat}设计理念")

        # 加入基础行动
        for action in base_actions:
            if action not in items:
                items.append(action)

        return items[:6]  # 最多6项，保持聚焦

    def _generate_expected_outcomes(
        self,
        direction: Dict[str, Any],
        diag_type: str,
        investigation: Dict[str, Any]
    ) -> List[str]:
        """生成具体可衡量的预期成果"""
        outcomes = []
        impact = direction.get("impact", "")

        if impact:
            outcomes.append(impact)

        # 基于调研的具体参考
        web = investigation.get("web_findings", [])
        valid_web = [r for r in web if "error" not in str(r)]

        if valid_web and diag_type in ["visual_design", "ux_interaction"]:
            # 参考竞品的具体做法
            titles = [r.get("title", "") for r in valid_web[:2] if r.get("title")]
            for t in titles:
                if len(t) < 60:
                    outcomes.append(f"参考：{t}")

        if not outcomes:
            outcomes.append(direction.get("description", "问题得到改善"))

        return outcomes

    def _generate_risks(self, direction: Dict[str, Any], diag_type: str) -> List[str]:
        """生成具体风险"""
        effort = direction.get("effort", "中")
        scope = direction.get("scope", "")

        risks = []
        if effort == "高":
            risks.append("改动面大，回归测试成本高")
            risks.append("可能影响现有用户体验")
        if effort == "中":
            risks.append("需要瀚峰确认设计方向后再继续")
            risks.append("部分效果依赖具体实现质量")
        if scope == "全局":
            risks.append("涉及多个模块，需要分阶段验证")

        if not risks:
            risks.append("效果可能需要多轮迭代才能达到预期")

        return risks

    def _generate_pros(
        self,
        direction: Dict[str, Any],
        diag_type: str,
        investigation: Dict[str, Any]
    ) -> List[str]:
        """生成具体优势"""
        impact = direction.get("impact", "")
        scope = direction.get("scope", "")

        pros = []
        if impact:
            pros.append(impact)

        if scope in ["局部（样式层）", "局部（组件层）", "局部（性能）"]:
            pros.append("改动范围可控，风险低")
            pros.append("可快速上线验证效果")
        elif scope in ["局部（交互动效）"]:
            pros.append("现代感大幅提升")
            pros.append("技术可复用")

        # 从竞品调研提取的借鉴点
        cases = investigation.get("similar_cases", [])
        for case in cases[:1]:
            cat = case.get("category", "")
            if cat:
                pros.append(f"借鉴{cat}方向的成功实践")

        if not pros:
            pros.append("有针对性解决当前问题")

        return pros

    def _generate_cons(self, direction: Dict[str, Any], diag_type: str) -> List[str]:
        """生成具体劣势"""
        effort = direction.get("effort", "中")
        scope = direction.get("scope", "")

        cons = []
        if effort == "高":
            cons.append("投入时间较长，需要分阶段执行")
        if effort == "中":
            cons.append("需要瀚峰参与设计确认")
        if scope == "全局（设计+实现）" or scope == "全局（UX+实现）":
            cons.append("属于较大改动，建议先做小范围验证")

        if not cons:
            cons.append("可能需要后续微调")

        return cons

    def _build_quick_win(
        self,
        problem: str,
        diag_type: str,
        tech_stack: Dict[str, Any]
    ) -> Plan:
        """生成一个低投入快速改进方案"""
        quick_actions = {
            "visual_design": ["统一CSS变量", "优化图片格式和尺寸", "字体层级整理"],
            "ux_interaction": ["按钮hover效果", "卡片点击反馈", "滚动行为优化"],
            "performance": ["图片懒加载", "字体子集化", "删除无用代码"],
            "content": ["精简Hero文案", "优化About段落"],
        }.get(diag_type, ["明确优化目标", "快速验证方向"])

        ts = tech_stack.get("frontend", "")
        ts_lower = ts.lower()

        action_items = []
        if "react" in ts_lower:
            action_items.append("React.lazy 路由分割（1小时）")
        if "vite" in ts_lower:
            action_items.append("vite build 分析 + 删除无用依赖（1小时）")
        if "css" in str(quick_actions).lower():
            action_items.append("建立 CSS 变量系统（2小时）")
        action_items.extend(quick_actions[:3])

        return Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="快速改进（1天内可上线）",
            description=f"低成本快速改进方案，针对：{problem[:60]}",
            pros=["投入时间少", "风险低，可快速回滚", "当天可上线验证"],
            cons=["效果可能有限", "可能需要后续进一步优化"],
            resource_estimate={
                "effort": "低",
                "scope": "局部",
                "automation": "高",
                "execution_style": "小步快跑"
            },
            risks=["效果可能不够彻底"],
            expected_outcomes=["问题有所改善，可作为后续深度改进的基础"],
            action_items=action_items[:5],
            scores=None,
            approved=None,
            approver_notes=None
        )

    def _generate_generic_plans(self, problem: str, diag_type: str) -> List[Plan]:
        """Fallback：生成通用三档方案"""
        return [
            Plan(
                plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                project_id="current",
                title="快速改进",
                description=f"低投入快速解决：{problem[:80]}",
                pros=["风险低", "快速启动", "易于回滚"],
                cons=["可能不是最优解"],
                resource_estimate={"effort": "低", "scope": "局部", "automation": "高", "execution_style": "小步快跑"},
                risks=["可能需要二次迭代"],
                expected_outcomes=["问题得到缓解"]
            ),
            Plan(
                plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                project_id="current",
                title="折中方案",
                description=f"在成本和效果间取得平衡：{problem[:80]}",
                pros=["平衡风险和收益", "更适合持续迭代"],
                cons=["两边都不完美"],
                resource_estimate={"effort": "中", "scope": "核心链路", "automation": "高", "execution_style": "先关键后扩展"},
                risks=["需要精细执行"],
                expected_outcomes=["较好解决问题"]
            ),
            Plan(
                plan_id=f"plan-{uuid.uuid4().hex[:8]}",
                project_id="current",
                title="全面改进",
                description=f"系统性解决：{problem[:80]}",
                pros=["根因处理更彻底", "长期收益更高"],
                cons=["改动面大", "验证成本高"],
                resource_estimate={"effort": "高", "scope": "全局", "automation": "中", "execution_style": "阶段推进"},
                risks=["影响现有功能"],
                expected_outcomes=["彻底解决问题"]
            ),
        ]
