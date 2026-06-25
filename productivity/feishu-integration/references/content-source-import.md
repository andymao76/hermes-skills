# 外部内容源导入飞书/本地知识库

飞书文档之外,以下内容是常见导入来源。

## 知识星球（zsxq.com）

需登录（已加入星球）后才能访问。

### MarkDownload 浏览器扩展（推荐单篇操作）

- **项目**: https://github.com/deathau/markdownload
- **安装**: Chrome Web Store 搜索 "MarkDownload - Markdown Web Clipper"
- **用法**:
  1. 浏览器登录知识星球
  2. 打开目标文章页面
  3. 点击扩展图标 → 弹出 Markdown 预览
  4. Download → 保存为 `.md` 文件
- **选中裁剪**: 选中页面部分文字再点扩展，只裁剪选中内容
- **Obsidian 集成**: 扩展设置中开启 Obsidian integration，配置 vault + 文件夹后右键 Send Tab to Obsidian
- **标题格式**: 支持 mixed-kebab、mixed_snake、obsidian-cal 等命名规则（v3.4.0）

### zsxq-spider（免费开源，可批量）

- **地址**: https://gitcode.com/gh_mirrors/zs/zsxq-spider
- **依赖**: Python 3.7+，需安装 wkhtmltox（PDF 生成引擎）
- **配置**: 需提供 Cookie（浏览器开发者工具获取）+ 星球 topic_id
- **输出**: PDF

### 星球助手（付费，功能最强）

- **地址**: https://github.com/wisdom-valley/planet-helper-release
- **功能**: 批量下载帖子/图片/附件，导出 Word/Markdown/PDF，本地搜索，离线备份
- **价格**: 需购买激活码（微信关注"智慧谷星球"）
- **平台**: Windows / Linux / macOS

## 飞书文档直接获取（无需 API）

公开分享的飞书文档 URL 加 `.md` 后缀即可获取 AI 友好的纯 Markdown 内容：

```
https://xxx.feishu.cn/docx/xxxxx.md
https://xxx.feishu.cn/wiki/xxxxx.md
```

这是飞书渲染页面的地址，与 Open API 导出是两条不同的路径。适合快速抓取单篇文档。
