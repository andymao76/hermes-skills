---
name: weather
description: Get current weather and forecasts (no API key required).
homepage: https://wttr.in/:help
metadata: {"clawdbot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather

Free weather services, no API keys needed. This skill follows the user's preferred
**beautiful table format** for all weather output.

## Open-Meteo (primary — JSON, reliable behind GFW)

Free, no key. Use this as the primary source (wttr.in is often unreachable from Chinese networks):

```bash
# Coordinate query (find lat/lon for the city first)
curl -s "https://api.open-meteo.com/v1/forecast?latitude=32.2&longitude=119.45&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_max,relative_humidity_2m_min&timezone=Asia/Shanghai&days=5"
```

Common city coordinates (China):
- 镇江: 32.2, 119.45
- 南京: 32.06, 118.8
- 北京: 39.9, 116.4
- 上海: 31.2, 121.5

### WMO Weather Code → Emoji Mapping

| Code | Meaning | Emoji |
|:----:|:--------|:----:|
| 0 | 晴天 | ☀️ |
| 1 | 少云 | 🌤️ |
| 2 | 多云 | ⛅ |
| 3 | 阴天 | ☁️ |
| 45,48 | 雾 | 🌫️ |
| 51,53 | 毛毛雨 | 🌦️ |
| 55 | 大雨 | 🌧️ |
| 61 | 小雨 | 🌦️ |
| 63 | 中雨 | 🌧️ |
| 65 | 大雨 | 🌧️ |
| 80 | 阵雨 | 🌦️ |
| 95,96,99 | 雷暴 | ⛈️ |

## wttr.in (fallback, may be blocked)

Quick one-liner:
```bash
curl -s "wttr.in/London?format=3"
```

Format codes: `%c` condition · `%t` temp · `%h` humidity · `%w` wind · `%l` location

## Output Format

User prefers **table-formatted weather output** with emoji and structured layout.

### Current conditions

```
| 项目 | 数据 |
|:---|:---:|
| 🌡️ 温度 | **24.1°C** |
| ☁️ 天气 | 阴天 |
| 💨 风速 | 7.3 km/h |
```

### Multi-day forecast table

Columns: 日期 | 天气图标+描述 | 高温(加粗) | 低温 | 💧降水 | 💨风力 | 💦湿度

```markdown
| 日期 | 天气 | 高温 | 低温 | 💧 降水 | 💨 风力 | 💦 湿度 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **📅 6/13 今天** | ☁️ 阴天 | **28.7°C** | 22.8°C | 0.0 mm | 17 km/h | 40~77% |
| **📅 6/14 周日** | 🌧️ 大雨 | **29.2°C** | 21.6°C | 2.1 mm | 19 km/h | 57~90% |
```

### Rules

1. Use **Open-Meteo** as primary data source (API not blocked in China)
2. Map WMO weathercode to emoji + Chinese description
3. Highlight today's row with **📅 今天**
4. **Bold** the high temperature column
5. Include 降水(mm) and 湿度 range columns
6. End with a **温馨提示** section with practical advice
7. City pairs the user follows: 镇江 + 南京 (can fetch both in one response)
