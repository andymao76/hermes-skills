# 已安装的社区工具状态

> 安装日期：2026-06-09
> 来源：awesome-hermes-agent (0xNyk)

## 1. web-search-plus (Plugin) ✅

| 属性 | 值 |
|------|-----|
| **仓库** | robbyczgw-cla/hermes-web-search-plus |
| **版本** | 2.4.0 |
| **安装位置** | `~/.hermes/plugins/web-search-plus/` |
| **状态** | ✅ 已启用（enabled） |
| **提供工具** | `web_search_plus`, `web_extract_plus` |
| **已配置 key** | TAVILY_API_KEY ✅ |
| **缺少 key** | SERPER_API_KEY, LINKUP_API_KEY, YOU_API_KEY（建议至少注册一个备用） |
| **测试结果** | 搜索正常，质量报告可用 |

**配置命令：**
```bash
cd ~/.hermes/plugins/web-search-plus
python3 setup.py setup --preset lean
python3 search.py --query "test" --quality-report
```

**注册免费备用 key：** https://serper.dev（2500次/月免费）

---

## 2. camofox-browser (Plugin) ✅

| 属性 | 值 |
|------|-----|
| **仓库** | jo-inc/camofox-browser |
| **版本** | 1.11.2 |
| **安装位置** | `~/.hermes/plugins/camofox-browser/` |
| **状态** | ✅ 已安装，服务器运行于 localhost:9377 |
| **Camoufox 浏览器** | v150.0.2-beta.25 (662MB)，`~/.cache/camoufox/` |
| **uBlock Origin** | ✅ 已安装 |
| **better-sqlite3** | ✅ 已编译 |
| **修复的 server.js bug** | Xvfb `await` 缺失（已 patch） |
| **提供工具** | 11 tools（camofox_create_tab, camofox_snapshot, camofox_click 等） |

**启动命令：**
```bash
cd ~/.hermes/plugins/camofox-browser
ALL_PROXY=http://127.0.0.1:7897 node server.js
```

**安装踩坑记录（重要）：**
- Node.js `fetch` (undici) **不识别** `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`，下载 Camoufox 662MB 需用 `curl -L --proxy` 绕过
- `camoufox-js` 的版本检查有 bug：`150.0.2-beta.25` 的 release 版本号中字母被转为负数，导致被判定为低于 `alpha.1` 触发清理。需 patch `dist/__version__.js` 的 `CONSTRAINTS`
- `better-sqlite3` 需手动 `node-gyp rebuild`（pnpm 不编译 C++ addon）
- 安装 `/scripts/postinstall.js` 在 pnpm 模式下触发的是 `npx camoufox-js fetch`，跳过手动下载需自行处理 addon（UBO）和 version.json
- 细节见 skill `community-plugin-install` 的 `references/camoufox-install-troubleshooting.md`

---

## 3. personal-api-skill (Skill) ⏳

| 属性 | 值 |
|------|-----|
| **仓库** | beiyuii/personal-api-skill |
| **版本** | 2.0.3 |
| **安装位置** | `~/.hermes/skills/personal-api-skill/` |
| **状态** | ✅ 已安装，未初始化 |

**初始化命令：**
```bash
export OBSIDIAN_VAULT_PATH=~/knowledge
bash ~/.hermes/skills/personal-api-skill/scripts/setup.sh
```

作用：在 ~/knowledge 中创建 ME.md（身份合同）和 AGENT.md（行为规范），把知识库变成 AI 可读的 identity 层。

---

## 4. nextcloud-skill (Skill) ⏳

| 属性 | 值 |
|------|-----|
| **仓库** | adnw-vinc/hermes-nextcloud |
| **安装位置** | `~/.hermes/skills/hermes-nextcloud/` |
| **状态** | ✅ 已安装，未配置服务器 |

**配置命令：**
```bash
python3 ~/.hermes/skills/hermes-nextcloud/scripts/setup.py
```

需要：Nextcloud 服务器地址 + App Password（Nextcloud Settings → Security → Create App Password）

---

## 5. incident-commander (Skill) ✅

| 属性 | 值 |
|------|-----|
| **仓库** | Lethe044/hermes-incident-commander |
| **安装位置** | `~/.hermes/skills/incident-commander/` |
| **状态** | ✅ 已安装，已启用 |

**触发关键词：** server down, high CPU, memory leak, disk full, service crash, deployment failure, alert firing, on-call page

**核心循环：** DETECT → TRIAGE → DIAGNOSE → REMEDIATE → VERIFY → DOCUMENT → LEARN

无额外配置需要，已就绪。
