---
name: weather-forecast
description: '查询任意地点的当前定位和5-7天天气预报。覆盖中国城市（weather.com.cn）、日本城市（JMA気象庁API）、及通用IP定位。输出结构化表格，含天气、温度、降水概率、风力、紫外线等关键指标。'
category: productivity
tags:
  - weather
  - forecast
  - location
  - ip-geolocation
  - jma
  - china-weather
triggers:
  - 天气
  - 天气预报
  - 定位
  - 所在城市
  - weather
  - forecast
---

# Weather Forecast Skill

查询当前所在位置及目标城市的天气预报。支持中国城市、日本城市（关东/东京优先）及通用IP定位。

## 触发词

"天气"、"天气预报"、"定位"、"所在城市"、"weather"、"forecast"

## 工作流

### 1. IP 定位（获取当前城市）

```bash
curl -s http://ip-api.com/json/
```

返回 JSON，关键字段：`city`, `regionName`, `country`, `lat`, `lon`, `timezone`

示例输出：
```json
{"status":"success","country":"Japan","regionName":"Tokyo","city":"Tokyo","lat":35.6895,"lon":139.692}
```

### 2. 日本城市天气 — JMA 気象庁 API

**API 端点（东京）：**
```
https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json
```
城市代码：东京=130000，替换代码可查其他地区。

**数据结构（两段 timeSeries）：**

| 层级 | 内容 | 覆盖范围 |
|------|------|---------|
| timeSeries[0] | 3天详细预报（天气描述、风向浪高） | 当天~后天 |
| timeSeries[1] | 当天逐6小时降水概率（4个时段） | 当天 00/06/12/18时 |
| timeSeries[2] | 当天最低/最高气温 | 当天 |
| timeSeries[3] (第2个JSON对象内) | 7天气温预报（含上下界） | 明天起7天 |

**天气代码对照：**
| 代码 | 天气 |
|------|------|
| 100 | 晴 |
| 101 | 晴れ時々くもり（晴间多云） |
| 111 | 晴れ/夜遅くくもり（晴/夜间转阴） |
| 200 | くもり（多云/阴） |
| 201 | くもり時々晴れ（阴间晴） |
| 202 | くもり時々雨（阴间雨） |
| 300/302 | 雨（雨） |

**气温字段（第2个JSON的timeSeries[1]）：**
```
tempsMin / tempsMax — 代表值
tempsMinUpper / tempsMaxUpper — 上界
tempsMinLower / tempsMaxLower — 下界
```

**降水概率字段：**
```
pops — 概率百分比数组
reliabilities — 可信度（A/B/C级，A=高，C=低）
```

### 3. 中国城市天气 — 中央气象台

**API 端点：**
```
https://www.weather.com.cn/weather/<citycode>.shtml
```

**城市代码查询：** 通过 web_search 搜索"镇江 天气预报 中央气象台"获取代码。
已知代码：镇江=101190301，可通过 weather.com.cn 域名格式拼接访问。

**返回内容：** web_extract 提取后可得结构化表格，包含：
- 日期、天气、温度范围、风力
- 生活指数（感冒/运动/过敏/穿衣/洗车/紫外线）
- 逐日紫外线强度提示

**备选来源：**
```
https://qq.ip138.com/weather/<province>/<city>_10tian.htm
```
示例：`https://qq.ip138.com/weather/jiangsu/zhenjiang_10tian.htm`

### 4. 通用天气查询

对于非中日城市，先用 web_search 搜索 `"<city> 5-day weather forecast <date>"` 获取可靠的天气预报网站，然后用 web_extract 提取详情。

## 输出格式

5天预报以表格呈现，包含：

| 日期 | 天气 | 温度 | 风力 | 备注 |
|------|------|------|------|------|
| 6/10 (周四) | ☁ 多云转阴 | 19~32°C | <3级 | 🌞紫外线强 |

附加关键提醒（高温预警、降水提示、大风、防晒建议）。

## Pitfalls

- **JMA API 返回两个 JSON 对象**（数组长度2），第一段是3天预报，第二段是7天周预报。需要分别解析两个 timeSeries。
- **JMA 天气代码** 不是标准的文字描述，需要对照代码表翻译。代码 200=くもり(cloudy)，不等同于"rain"。
- **中国城市代码** 各地不同，不可硬编码。通过搜索获取或从 URL 模式推断。
- **IP 定位服务** `ip-api.com` 使用 HTTP（非 HTTPS），在安全审计环境中可能需要用户批准。
- **天气网站可能反爬**，web_extract 失败时使用 web_search 找备选来源。
- **JMA 气温上下界** 使用 tempsMinUpper/tempsMinLower 而非单一值，用"代表值 [下界~上界]" 格式呈现更准确。
- **时区注意**：JMA 返回 JST (UTC+9)，中国天气网站返回 CST (UTC+8)，用户所在时区以 IP 定位结果为准。
