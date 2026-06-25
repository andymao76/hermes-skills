# Resume / Personal CV Generation

Generate a structured professional resume (.docx) by composing system information, work history, and troubleshooting records.

## Data Sources to Scan

| Source | What to extract | Tool |
|--------|----------------|------|
| Hardware | CPU/cores, RAM, disk layout, network interfaces | `cat /proc/cpuinfo`, `free -h`, `lsblk`, `ip -br addr` |
| OS | Ubuntu version, kernel | `cat /etc/os-release`, `uname -a` |
| Hermes status | Version, provider, models, channels, services | `hermes status` |
| Cron jobs | All scheduled tasks | `hermes cron list` |
| Skills list | Skill categories and counts | `ls ~/.hermes/skills/` |
| Config | MCP servers, messaging, plugins | `cat ~/.hermes/config.yaml` (relevant sections) |
| Knowledge base | Vault structure, troubleshooting records | `ls ~/knowledge/` and sub-dirs |
| Session history | Recent work, project activity | `session_search()` |
| Memory | User profile, preferences | Already in context |

## Document Structure (Professional Resume)

| Section | Content | Type |
|---------|---------|------|
| Title page | Name, subtitle, date | Centered heading |
| 一、个人信息 | Name, contact (leave placeholders) | 2x4 table |
| 二、专业概要 | 1-2 paragraph professional summary | Paragraph |
| 三、核心技能 | Skill domain × specifics × proficiency | 3-column table (dark header) |
| 四、当前系统架构 | Hardware table + software stack + network topology | Tables + ASCII art |
| 五、系统搭建过程 | Numbered steps for each major subsystem | Numbered lists |
| 六、典型排错经验 | Fault × Root cause × Solution table | 4-column table |
| 七、工作经历 | Chronological experience entries | Headed sections with bullets |
| 八、技能库/项目 | Categories table + project table | Tables |
| 九、自我评价 | Key strengths | Bulleted paragraphs |

## Styling Constants

```python
HEADER_COLOR = '1F4E79'     # Dark blue header background
ALT_ROW_COLOR = 'E8F0FE'    # Light blue alternating rows
TITLE_COLOR = (31, 78, 121)  # RGB for title text
BODY_FONT = '微软雅黑'       # Chinese font (or 'SimSun')
HEADING_FONT = '微软雅黑'    # Heading Chinese font (or 'SimHei')
```

## Key Helper Pattern (None-safe rPr)

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cn_font(run, cn_font='微软雅黑', en_font='Arial'):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
```

## Verification

```python
import os
output_path = '~/个人简历.docx'
path = os.path.expanduser(output_path)
doc.save(path)
print(f'Saved: {path} ({os.path.getsize(path)/1024:.1f} KB)')
# Also verify with:
import docx
d = docx.Document(path)
print(f'Paras: {len(d.paragraphs)}, Tables: {len(d.tables)}')
```
