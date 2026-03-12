
---

# 📦 GitHub Repo

專案名稱建議

```
ai-agent-skills-workshop
```

副標題

```
Learn AI Skills, CLI Automation and Agent Workflow
```

---

# 📁 Repo 完整結構

```
ai-agent-skills-workshop
│
├─ README.md
├─ requirements.txt
├─ main.py
│
├─ ai_cli/
│   ├─ __init__.py
│   ├─ outline_parser.py
│   ├─ slide_generator.py
│   └─ ai_outline_generator.py
│
├─ agent/
│   └─ workflow.py
│
├─ skills/
│   ├─ slide-writer/
│   │   └─ SKILL.md
│   │
│   ├─ email-writer/
│   │   └─ SKILL.md
│   │
│   └─ report-writer/
│       └─ SKILL.md
│
├─ examples/
│   └─ outline.md
│
├─ datasets/
│   └─ sales.csv
│
├─ templates/
│   └─ default.json
│
├─ docs/
│   ├─ workshop-slides.md
│   └─ lab-guide.md
│
└─ outputs/
```

---

# README.md

```markdown
# AI Agent Skills Workshop v3

Learn how to build AI automation tools using:

- AI Skills
- CLI tools
- Agent workflows

## Install

pip install -r requirements.txt

## Generate slides

python main.py generate examples/outline.md

## AI generate slides

python main.py ai "AI Agent Introduction"

## Run Agent Workflow

python main.py agent "AI for Marketing"
```

---

# requirements.txt

```
python-pptx
typer
rich
openai
pandas
matplotlib
```

---

# main.py

```python
import typer

from ai_cli.outline_parser import parse_outline
from ai_cli.slide_generator import create_ppt
from ai_cli.ai_outline_generator import generate_outline
from agent.workflow import run_agent

app = typer.Typer()

@app.command()
def generate(file: str):

    slides = parse_outline(file)

    create_ppt(slides)

    print("Slides generated")


@app.command()
def ai(topic: str):

    outline = generate_outline(topic)

    with open("generated_outline.md","w") as f:
        f.write(outline)

    slides = parse_outline("generated_outline.md")

    create_ppt(slides)

    print("AI slides generated")


@app.command()
def agent(topic: str):

    run_agent(topic)


if __name__ == "__main__":
    app()
```

---

# ai_cli/outline_parser.py

```python
def parse_outline(file_path):

    slides = []
    current = None

    with open(file_path) as f:

        for line in f:

            line = line.strip()

            if line.startswith("# "):

                slides.append({
                    "title": line[2:],
                    "bullets":[]
                })

                current = slides[-1]

            elif line and current:

                current["bullets"].append(line)

    return slides
```

---

# ai_cli/slide_generator.py

```python
from pptx import Presentation

def create_ppt(slides):

    prs = Presentation()

    for s in slides:

        slide = prs.slides.add_slide(prs.slide_layouts[1])

        slide.shapes.title.text = s["title"]

        body = slide.placeholders[1].text_frame

        for b in s["bullets"]:

            p = body.add_paragraph()
            p.text = b

    prs.save("outputs/presentation.pptx")
```

---

# ai_cli/ai_outline_generator.py

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_outline(topic):

    prompt = f"""
Create presentation outline.

Topic: {topic}

Format:

# Title

## Slide
bullet
bullet
bullet
"""

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return r.choices[0].message.content
```

---

# agent/workflow.py

```python
from ai_cli.ai_outline_generator import generate_outline
from ai_cli.outline_parser import parse_outline
from ai_cli.slide_generator import create_ppt

def run_agent(topic):

    print("Agent start")

    outline = generate_outline(topic)

    with open("agent_outline.md","w") as f:
        f.write(outline)

    slides = parse_outline("agent_outline.md")

    create_ppt(slides)

    print("Agent finished")
```

---

# Skill 範例

## skills/slide-writer/SKILL.md

```
Role:
You are a presentation expert

Task:
Create slide outline

Rules:
Each slide 3 bullets
```

---

## skills/email-writer/SKILL.md

```
Role:
Business email expert

Task:
Write professional email
```

---

# examples/outline.md

```
# AI Skills Workshop

## What is AI Skill
Reusable prompt
Automation
Workflow

## Skill Architecture
Prompt
Skill
Skill Library
Agent
```

---

# datasets/sales.csv

```
month,revenue
Jan,10000
Feb,12000
Mar,15000
Apr,17000
May,21000
```

---

# docs/lab-guide.md

```
Workshop Lab

1 Generate slides

python main.py generate examples/outline.md

2 AI generate slides

python main.py ai "AI Agent"

3 Run agent workflow

python main.py agent "AI for Marketing"
```

---

# 🎓 教學效果（v3）

這個 Repo 可以同時教：

| 主題         | 技術                 |
| ---------- | ------------------ |
| AI Skill   | Prompt engineering |
| CLI Tool   | Typer              |
| Automation | Python             |
| Agent      | Workflow           |
| AI         | OpenAI API         |

---

# 🚀 v3 的最大亮點

CLI 會變成：

```
python main.py generate
python main.py ai
python main.py agent
```

讓學員理解：

```
Prompt
↓
Skill
↓
Tool
↓
Agent
```

---


---
> © 2026 paddyyang (paddyyang.igs.com.tw@gmail.com) | MIT License
