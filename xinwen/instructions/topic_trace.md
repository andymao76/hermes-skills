# 话题追踪指令

## 触发条件
用户说"追踪XXX"、"关注XXX"、"XXX有什么新消息"

## 执行步骤

### 模式一：关键词追踪
用户指定关键词时：
```bash
python3 scripts/intelligence.py --mode trace --keyword "GPT-5"
```

### 模式二：领域深挖
用户指定领域时：
```bash
python3 scripts/intelligence.py --mode topic --topic AI深度
```

支持的话题：
- 全球科技
- 开源社区
- 国内资讯
- 金融财经
- AI深度

### 模式三：生成追踪命令
用户对某条情报说"追踪"时，使用tracker.py生成追踪命令模板：
```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from tracker import generate_track_command
import json
item = {'title': '用户选中的情报标题', 'source': '来源', 'level': '🔴关键'}
print(json.dumps(generate_track_command(item), ensure_ascii=False, indent=2))
"
```

然后将输出的命令模板交给主助手执行topic_tracking技能。

## 注意事项
- 关键词追踪使用全量抓取后过滤，耗时与daily模式相同
- 领域深挖只抓取对应分类的信源，速度更快
