# JMA 気象庁 Weather Code Reference

Source: Japan Meteorological Agency forecast JSON API

## Primary Weather Codes

| Code | Japanese | English | Chinese |
|------|----------|---------|---------|
| 100 | 晴 | Sunny | 晴 |
| 101 | 晴れ 時々 くもり | Sunny, occasionally cloudy | 晴间多云 |
| 102 | 晴れ 一時 雨 | Sunny, chance of rain | 晴/偶有雨 |
| 103 | 晴れ 時々 雨 | Sunny, occasional rain | 晴间雨 |
| 104 | 晴れ 一時 雪 | Sunny, chance of snow | 晴/偶有雪 |
| 105 | 晴れ 時々 雪 | Sunny, occasional snow | 晴间雪 |
| 106 | 晴れ 一時 雨 後 雪 | Sunny, rain then snow | 晴/雨后转雪 |
| 107 | 晴れ 一時 雪 後 雨 | Sunny, snow then rain | 晴/雪后转雨 |
| 108 | 晴れ 一時 雨 後 雷 | Sunny, rain then thunder | 晴/雨后雷 |
| 110 | 晴れ のち くもり | Sunny, then cloudy | 晴转阴 |
| 111 | 晴れ 夜遅く くもり | Sunny, becoming cloudy late night | 晴/夜间转阴 |
| 112 | 晴れ のち 雨 | Sunny, then rain | 晴转雨 |
| 113 | 晴れ のち 雪 | Sunny, then snow | 晴转雪 |
| 114 | 晴れ のち 雨 後 くもり | Sunny, rain, then cloudy | 晴/雨后转阴 |
| 115 | 晴れ のち 雪 後 くもり | Sunny, snow, then cloudy | 晴/雪后转阴 |
| 120 | 晴れ 朝の内 雨 | Sunny, rain in morning | 晴/早晨有雨 |
| 121 | 晴れ 朝の内 雪 | Sunny, snow in morning | 晴/早晨有雪 |
| 130 | 朝の内 晴れ 後 くもり | Sunny in morning, then cloudy | 早晨晴转阴 |
| 131 | 晴れ 昼頃から 雨 | Sunny, rain around noon | 晴/中午前后有雨 |
| 132 | 晴れ 昼頃から 雪 | Sunny, snow around noon | 晴/中午前后有雪 |
| 140 | 晴れ 時々 雨 雷を伴う | Sunny, occasional rain with thunder | 晴间雨/伴雷 |
| 200 | くもり | Cloudy | 多云/阴 |
| 201 | くもり 時々 晴れ | Cloudy, occasionally sunny | 阴间晴 |
| 202 | くもり 時々 雨 | Cloudy, occasional rain | 阴间雨 |
| 203 | くもり 時々 雪 | Cloudy, occasional snow | 阴间雪 |
| 204 | くもり 一時 雨 | Cloudy, chance of rain | 阴/偶有雨 |
| 206 | くもり 一時 雪 | Cloudy, chance of snow | 阴/偶有雪 |
| 207 | くもり 一時 雨 後 雪 | Cloudy, rain then snow | 阴/雨后转雪 |
| 208 | くもり 一時 雪 後 雨 | Cloudy, snow then rain | 阴/雪后转雨 |
| 209 | くもり 一時 雨 後 雷 | Cloudy, rain then thunder | 阴/雨后雷 |
| 210 | くもり のち 晴れ | Cloudy, then sunny | 阴转晴 |
| 211 | くもり のち 雨 | Cloudy, then rain | 阴转雨 |
| 212 | くもり のち 雪 | Cloudy, then snow | 阴转雪 |
| 214 | くもり 夜遅く 雨 | Cloudy, rain late night | 阴/夜间有雨 |
| 220 | くもり 朝の内 雨 | Cloudy, rain in morning | 阴/早晨有雨 |
| 221 | くもり 朝の内 雪 | Cloudy, snow in morning | 阴/早晨有雪 |
| 230 | くもり 昼頃から 雨 | Cloudy, rain around noon | 阴/中午前后有雨 |
| 231 | くもり 昼頃から 雪 | Cloudy, snow around noon | 阴/中午前后有雪 |
| 240 | くもり 時々 雨 雷を伴う | Cloudy, occasional rain with thunder | 阴间雨/伴雷 |
| 250 | くもり 時々 雪 雷を伴う | Cloudy, occasional snow with thunder | 阴间雪/伴雷 |
| 260 | くもり 一時 雨 後 雪 雷を伴う | Cloudy, rain then snow with thunder | 阴/雨后雪/伴雷 |
| 270 | くもり 一時 雪 後 雨 雷を伴う | Cloudy, snow then rain with thunder | 阴/雪后雨/伴雷 |
| 281 | くもり 後 大雨 | Cloudy, then heavy rain | 阴转大雨 |
| 282 | くもり 後 大雪 | Cloudy, then heavy snow | 阴转大雪 |
| 300 | 雨 | Rain | 雨 |
| 301 | 雨 のち くもり | Rain, then cloudy | 雨转阴 |
| 302 | 雨 夜のはじめ頃 くもり | Rain, becoming cloudy early night | 雨/夜间转阴 |
| 303 | 雨 時々 止む | Rain, occasionally stopping | 雨/时停时下 |
| 304 | 雨 一時 止む | Rain, chance of stopping briefly | 雨/偶有停歇 |
| 306 | 雨 のち 晴れ | Rain, then sunny | 雨转晴 |
| 308 | 雨 のち 雪 | Rain, then snow | 雨转雪 |
| 309 | 雨 のち 雪 後 晴れ | Rain, snow, then sunny | 雨/雪后转晴 |
| 311 | 雨 のち 晴れ 後 くもり | Rain, sunny, then cloudy | 雨/晴后转阴 |
| 313 | 雨 のち 雪 後 くもり | Rain, snow, then cloudy | 雨/雪后转阴 |
| 314 | 雨 時々 雪 | Rain, occasional snow | 雨间雪 |
| 320 | 大雨 | Heavy rain | 大雨 |
| 321 | 大雨 のち 雨 | Heavy rain, then rain | 大雨转雨 |
| 322 | 大雨 のち くもり | Heavy rain, then cloudy | 大雨转阴 |
| 323 | 大雨 のち 晴れ | Heavy rain, then sunny | 大雨转晴 |
| 324 | 大雨 時々 雨 | Heavy rain, occasional rain | 大雨间雨 |
| 325 | 大雨 時々 止む | Heavy rain, occasionally stopping | 大雨/时停时下 |
| 326 | 大雨 一時 止む | Heavy rain, chance of stopping | 大雨/偶停 |
| 350 | 雨 雷を伴う | Rain with thunder | 雷雨 |
| 361 | 大雨 雷を伴う | Heavy rain with thunder | 大雨伴雷 |
| 370 | 雨 のち 大雨 雷を伴う | Rain, heavy rain with thunder | 雨后大雨伴雷 |
| 400 | 雪 | Snow | 雪 |
| 401 | 雪 のち くもり | Snow, then cloudy | 雪转阴 |
| 402 | 雪 のち 晴れ | Snow, then sunny | 雪转晴 |
| 403 | 雪 時々 止む | Snow, occasionally stopping | 雪/时停时下 |
| 405 | 大雪 | Heavy snow | 大雪 |
| 406 | 大雪 のち 雪 | Heavy snow, then snow | 大雪转雪 |
| 407 | 大雪 のち くもり | Heavy snow, then cloudy | 大雪转阴 |
| 408 | 大雪 のち 晴れ | Heavy snow, then sunny | 大雪转晴 |
| 411 | 雪 時々 雨 | Snow, occasional rain | 雪间雨 |
| 413 | 雪 のち 雨 後 くもり | Snow, rain, then cloudy | 雪/雨后转阴 |
| 414 | 雪 のち 雨 | Snow, then rain | 雪转雨 |

## Reliability Ratings (週間天気予報)

| 等级 | 含义 |
|------|------|
| A | 高可信度（予報が大きく変わる可能性が低い） |
| B | 中可信度（予報が変わる可能性がある） |
| C | 低可信度（予報が変わる可能性が高い、変動注意） |

## API 结构速查

```
GET https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json
```

响应为 JSON 数组 `[forecast_3day, forecast_7day]`：

**forecast_3day (index 0)**
- `timeSeries[0]` — 3天天气描述、风向、波浪
- `timeSeries[1]` — 当天逐6h降水概率（CST 00/06/12/18各时段）
- `timeSeries[2]` — 当天最低/最高气温

**forecast_7day (index 1)**
- `timeSeries[0]` — 7天天气代码 + 降水概率 + 可信度
- `timeSeries[1]` — 7天气温（tempsMin/tempsMax + Upper/Lower bounds）

重要城市代码：东京=130000, 大阪=270000, 名古屋=230000, 福冈=400000, 札幌=010000
