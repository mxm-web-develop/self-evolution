# Self-Evolution

An AI-powered project evolution system that guides projects through **investigation → diagnosis → planning → execution → learning** — a complete closed loop.

---

## Installation

### Step 1: Download

**Option A: Git clone**
```bash
cd ~/.openclaw/skills
git clone https://github.com/mxm-web-develop/self-evolution.git
```

**Option B: Download ZIP**
Download the ZIP from the [GitHub repo](https://github.com/mxm-web-develop/self-evolution) and extract to `~/.openclaw/skills/self-evolution/`

### Step 2: Place in the correct location

OpenClaw searches for skills in three locations (in order of precedence):

| Location | Scope | Command |
|----------|-------|---------|
| `~/.openclaw/workspace/skills/` | Current workspace only | `mkdir -p ~/.openclaw/workspace/skills` |
| `~/.openclaw/skills/` | All agents on this machine | `mkdir -p ~/.openclaw/skills` |
| Built-in bundled skills | OpenClaw internal | No action needed |

**Recommended: put it in `~/.openclaw/skills/`** so any workspace can use it:

```bash
mv self-evolution ~/.openclaw/skills/
```

To verify installation, just talk to OpenClaw naturally:
```
analyze my mxmaiwebsite project
what projects do I have
help me set up a new project
```

---

## How It Works

### Step 1: Tell me your project name

No commands to memorize. Just say what you want:

```
optimize mxmaiwebsite
check on pixgen
look at supermxmai
```

**What happens:**
1. I scan the workspace to find matching projects
2. I ask you to confirm: "You mean the project at `/path/to/mxmaiwebsite`?"
3. I check whether this project already has a record

---

### Step 2: Answer a few questions (first time only)

If it's a new project or information is incomplete, I'll ask specific questions based on what I found in your code:

```
I see your site uses React + Vite,
and the hero currently says "Full-stack Developer".
1. Do you want visitors to immediately understand what you do? Or is showcasing work more important?
2. You have a fox mascot — do you want to strengthen it or tone it down?
3. How's the page load speed in your experience?
```

Each question is grounded in your actual code, not generic. After you answer, I build a project profile.

---

### Step 3: I research and diagnose

I will:
- Scan your code structure
- Research what mature projects in your category look like
- Assess your project's current maturity level
- Identify the highest-priority gaps

You get a clear report:

```
Project maturity: Relatively mature

Highest priority gaps (by order):
1. Brand expression & positioning clarity (gap: high)
2. Visual system & consistency (gap: high)
3. Performance & load quality (gap: high)
4. Interaction feedback & browsing smoothness (gap: medium-high)
...
```

---

### Step 4: I present multiple plans to choose from

Each improvement direction gets its own plan, containing:
- Current state vs. maturity standard
- Concrete action items

```
📋 Plan A: Brand Expression & Positioning
  Current: Brand signals are fragmented, visitors can't pin down your positioning
  Target: Visitors understand what you do and why you're trustworthy within 5 seconds
  Actions:
  • Rewrite the hero value proposition
  • Define signature projects and capability tags
  • Add clear collaboration/contact entry point
```

---

### Step 5: You approve, I execute

```
approve plan A
```

After you confirm, I start executing. Results get written back to the project record.

---

### Step 6: I learn automatically

After each round, insights are written to the shared memory:
- Which improvements had the most impact
- Which approaches worked best for this project type

Future projects can draw on this without starting from scratch.

---

## Example Commands

| You say | I do |
|---------|------|
| `optimize mxmaiwebsite` | Identify project → Confirm → Start analysis |
| `check on pixgen` | Identify project → Check records → Continue |
| `build a new AI writing backend` | New project → Onboarding → Start |
| `what projects do I have` | List all projects with status |
| `approve plan B` | Execute plan B |
| `don't run it yet, what else needs work` | Continue analysis |

---

## Directory Structure

```
~/.openclaw/skills/self-evolution/
├── SKILL.md                  # OpenClaw Skill entry point
├── README.md                 # This file
├── README_zh.md              # 中文版 / Chinese version
├── memory/                   # Shared cross-project memory
│   ├── insights/            # General insights
│   ├── project-types/        # Experience by project type
│   └── sessions/            # Per-session analysis records
├── projects/                # Project-isolated data
│   └── {project-id}/
│       ├── profile.md        # Project profile
│       ├── config.yaml      # Project config
│       ├── state.json       # Runtime state
│       └── analysis/
│           ├── investigation.md
│           ├── gaps.md
│           ├── plans/
│           └── outcomes/
├── scripts/                # Executable scripts
└── references/             # Reasoning framework prompt templates
```

---

## How the Skill Triggers

OpenClaw automatically scans all directories under `~/.openclaw/skills/` and loads the `SKILL.md` in each one.

The `description` field in the YAML frontmatter controls when the skill activates:

```yaml
---
name: self-evolution
description: Project self-evolution analysis... triggers when the user wants to analyze, diagnose, plan, or optimize a project.
---
```

When you say something like "analyze", "optimize", "research", or "check on" a project, OpenClaw loads the self-evolution skill automatically.

---

## FAQ

**Q: Do I need to type `/evolve xxx` every time?**
No. Just describe what you want naturally, like "check on my mxmaiwebsite project".

**Q: Can I track multiple projects at once?**
Yes. I keep track of each project's state and history. Just mention the project name and I'll pick up where we left off.

**Q: My project is on GitHub — how do I connect it?**
Just tell me, like "connect my GitHub project mxm-web-develop/somerepo" and I'll scan it to understand the structure.

**Q: Can I start from scratch with a new project?**
Yes. Tell me what you want to build, I'll ask a few key questions to understand your goals, then start the analysis.

**Q: Nothing happened after I installed the skill. What do I do?**
Say "reload skills" or "refresh skills" in OpenClaw, or restart the OpenClaw gateway.

---

## Maintainer

Zhang Hanfeng (mxmai)
