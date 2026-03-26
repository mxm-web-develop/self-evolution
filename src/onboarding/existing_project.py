"""
已有项目接入初始化器（最小版）
扫描项目目录，读取配置，生成基础项目画像
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from .state import OnboardingSession, OnboardingPhase
from .index_manager import ProjectIndex
from . import templates


def make_project_id(name: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
    slug = "-".join(slug.lower().split())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or "project"


class ExistingProjectScanner:
    """已有项目扫描器（最小版）"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).expanduser().resolve()

    # ── 扫描方法 ────────────────────────────────────────────────

    def scan(self) -> Dict[str, Any]:
        """
        执行完整扫描，返回项目画像字典
        """
        return {
            "project_path": str(self.project_path),
            "project_name": self._detect_name(),
            "tech_stack": self._detect_tech_stack(),
            "readme": self._read_readme(),
            "package_info": self._detect_packages(),
            "structure": self._detect_structure(),
            "health": self._assess_health(),
        }

    def _detect_name(self) -> str:
        """从目录名推断项目名"""
        return self.project_path.name

    def _detect_tech_stack(self) -> Dict[str, Any]:
        """检测技术栈"""
        ts: Dict[str, Any] = {
            "languages": [],
            "frameworks": [],
            "package_manager": None,
            "test_framework": None,
            "has_ci": False,
        }

        p = self.project_path
        langs = set()
        frameworks = set()

        # 文件扩展名 → 语言
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript (React)",
            ".tsx": "TypeScript (React)",
            ".go": "Go",
            ".rs": "Rust",
            ".java": "Java",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".vue": "Vue",
            ".svelte": "Svelte",
        }

        # 框架检测
        framework_patterns = {
            "Next.js": ["next.config", "package.json"],
            "React": ["package.json"],
            "Vue": ["package.json"],
            "FastAPI": ["main.py"],
            "Django": ["manage.py"],
            "Flask": ["app.py", "wsgi.py"],
            "Express": ["package.json"],
            "Spring": ["pom.xml"],
            "Gin": ["go.mod"],
            "Rails": ["Gemfile"],
        }

        for root, dirs, files in os.walk(p):
            # Skip hidden/node_modules/.venv
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build')]

            for f in files:
                ext = Path(f).suffix
                if ext in ext_map:
                    langs.add(ext_map[ext])

                # Framework detection
                if f == "package.json":
                    frameworks.add("Next.js / React")
                    frameworks.add("Node.js")
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8") as pf:
                            pkg = json.load(pf)
                            deps = pkg.get("dependencies", {})
                            dev = pkg.get("devDependencies", {})
                            all_deps = {**deps, **dev}
                            if "next" in all_deps:
                                frameworks.add("Next.js")
                            elif "react" in all_deps:
                                frameworks.add("React")
                            if "express" in all_deps:
                                frameworks.add("Express")
                            ts["package_manager"] = "npm"
                    except:
                        pass

                if f == "pyproject.toml":
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8") as pf:
                            content = pf.read()
                            if "fastapi" in content.lower():
                                frameworks.add("FastAPI")
                            if "django" in content.lower():
                                frameworks.add("Django")
                            if "flask" in content.lower():
                                frameworks.add("Flask")
                            ts["package_manager"] = "pip / uv"
                    except:
                        pass

                if f == "requirements.txt":
                    ts["package_manager"] = "pip"
                    frameworks.add("Python")

                if f == "go.mod":
                    frameworks.add("Go (Gin/Fiber)")
                    ts["package_manager"] = "go mod"

                if f == "Cargo.toml":
                    frameworks.add("Rust")
                    ts["package_manager"] = "cargo"

                if f == "Gemfile":
                    frameworks.add("Ruby on Rails")
                    ts["package_manager"] = "bundle"

                # CI detection
                if f in (".github/workflows/main.yml", ".github/workflows/ci.yml"):
                    ts["has_ci"] = True
                if f == "Makefile":
                    ts["has_ci"] = True

                # Test framework detection
                if f in ("vitest.config.ts", "vitest.config.js"):
                    ts["test_framework"] = "Vitest"
                if f == "pytest.ini" or "test_" in f or f.startswith("test_"):
                    ts["test_framework"] = "pytest"
                if f == "jest.config.js" or f == "jest.config.ts":
                    ts["test_framework"] = "Jest"

        ts["languages"] = sorted(list(langs))
        ts["frameworks"] = sorted(list(frameworks))
        return ts

    def _read_readme(self) -> Optional[str]:
        """读取 README.md"""
        for name in ("README.md", "README.txt", "README"):
            readme_path = self.project_path / name
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        content = f.read(2000)  # limit to 2000 chars
                    return content
                except:
                    pass
        return ""

    def _detect_packages(self) -> Dict[str, Any]:
        """读取包管理文件"""
        info = {}
        p = self.project_path

        if (p / "package.json").exists():
            try:
                with open(p / "package.json", "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                info["package_json"] = {
                    "name": pkg.get("name", ""),
                    "version": pkg.get("version", ""),
                    "scripts": list(pkg.get("scripts", {}).keys()),
                }
            except:
                pass

        if (p / "requirements.txt").exists():
            try:
                with open(p / "requirements.txt", "r", encoding="utf-8") as f:
                    deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                info["requirements_txt"] = {
                    "count": len(deps),
                    "preview": deps[:5],
                }
            except:
                pass

        if (p / "pyproject.toml").exists():
            info["pyproject_toml"] = True

        if (p / "go.mod").exists():
            info["go_mod"] = True

        return info

    def _detect_structure(self) -> Dict[str, Any]:
        """检测目录结构"""
        p = self.project_path
        items = []
        try:
            items = [d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith('.')]
        except:
            pass
        return {
            "top_level_dirs": items[:10],
        }

    def _assess_health(self) -> Dict[str, Any]:
        """评估项目健康度（最小版）"""
        health: Dict[str, Any] = {
            "has_readme": False,
            "has_tests": False,
            "has_ci": False,
            "has_git": False,
        }
        p = self.project_path
        health["has_readme"] = any((p / f).exists() for f in ("README.md", "README.txt"))
        health["has_tests"] = any(
            (p / d).exists()
            for d in ("tests", "test", "__tests__", "specs")
        )
        health["has_ci"] = (p / ".github" / "workflows").exists() or (p / "Makefile").exists()
        health["has_git"] = (p / ".git").exists()
        return health


class ExistingProjectInitializer:
    """已有项目接入初始化器"""

    def __init__(self, base_path: str, index: ProjectIndex):
        self.base_path = Path(base_path)
        self.index = index

    def initialize(self, project_path: str) -> tuple[OnboardingSession, Dict[str, Any]]:
        """
        扫描已有项目并初始化画像。
        返回 (session, scan_result)
        """
        scanner = ExistingProjectScanner(project_path)
        scan_result = scanner.scan()

        project_id = make_project_id(scan_result["project_name"])
        # 避免重复，追加后缀
        if self.index.project_exists(project_id):
            project_id = f"{project_id}-{len(self.index.list_projects())}"

        session = OnboardingSession(
            project_id=project_id,
            project_type="existing",
            phase=OnboardingPhase.COMPLETED,
            name=scan_result["project_name"],
            project_path=project_path,
        )
        session.add_history("scanned", f"scanned {project_path}")

        # 写入文件
        project_dir = self.base_path / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # state.json
        state_data = templates.build_state_json(session, {
            "tech_stack": scan_result["tech_stack"],
        })
        with open(project_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

        # profile.md（整合项目画像 + 用户目标 + 竞品参考）
        profile_md = templates.build_profile_md(session, {
            "lang": ", ".join(scan_result["tech_stack"].get("languages", [])),
            "framework": ", ".join(scan_result["tech_stack"].get("frameworks", [])),
            "package_manager": scan_result["tech_stack"].get("package_manager", ""),
            "test_framework": scan_result["tech_stack"].get("test_framework", ""),
            "ci_cd": "✅" if scan_result["tech_stack"].get("has_ci") else "❌",
        })
        goals_md = templates.build_user_goals_md(session)
        benchmarks_md = templates.build_competitor_benchmarks_md(session)
        merged_profile = profile_md.rstrip() + "\n\n## 用户目标\n\n" + goals_md.strip() + "\n\n## 竞品/标杆参考\n\n" + benchmarks_md.strip() + "\n"
        with open(project_dir / "profile.md", "w", encoding="utf-8") as f:
            f.write(merged_profile)

        # optimization-roadmap.md
        roadmap_md = templates.build_optimization_roadmap_md(session)
        with open(project_dir / "optimization-roadmap.md", "w", encoding="utf-8") as f:
            f.write(roadmap_md)

        # health-report.md（扫描报告）
        health_md = self._make_health_report_md(scan_result)
        with open(project_dir / "health-report.md", "w", encoding="utf-8") as f:
            f.write(health_md)

        # 更新 index.json
        idx_entry = self.index.make_project_entry(
            project_id=project_id,
            name=scan_result["project_name"],
            project_path=project_path,
            project_type="existing",
            description="",
        )
        idx_entry["onboarding_completed"] = True
        idx_entry["tech_stack"] = scan_result["tech_stack"]
        try:
            self.index.add_project(idx_entry)
        except ValueError:
            self.index.update_project(project_id, idx_entry)

        return session, scan_result

    def _make_health_report_md(self, scan: Dict[str, Any]) -> str:
        from datetime import datetime
        ts = scan["tech_stack"]
        health = scan["health"]

        pkg_items = []
        for k, v in scan.get("package_info", {}).items():
            pkg_items.append(f"- `{k}`: {v}")

        return f"""# 项目健康度扫描报告

> 项目：{scan['project_name']}
> 路径：{scan['project_path']}
> 扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 技术栈

| 类型 | 值 |
|---|---|
| 语言 | {', '.join(ts.get('languages', []) or ['未知'])} |
| 框架 | {', '.join(ts.get('frameworks', []) or ['未知'])} |
| 包管理 | {ts.get('package_manager', '未知')} |
| 测试框架 | {ts.get('test_framework', '未知')} |
| CI/CD | {'✅ 有' if ts.get('has_ci') else '❌ 无'} |

## 项目结构

- 顶层目录：`{', '.join(scan['structure'].get('top_level_dirs', []))}`

## 健康度

| 指标 | 状态 |
|---|---|
| README | {'✅' if health.get('has_readme') else '❌'} |
| 测试目录 | {'✅' if health.get('has_tests') else '❌'} |
| CI/CD | {'✅' if health.get('has_ci') else '❌'} |
| Git | {'✅' if health.get('has_git') else '❌'} |

## README 预览

```
{(scan.get('readme') or '(无 README)')[:500]}
```

## 下一步

请补充以下信息以完善项目画像：
1. 项目目标（这个项目要做什么）
2. 对标竞品
3. 优化优先级

这些信息可通过编辑 `profile.md` 或运行 `/evolve` 补充。
"""
