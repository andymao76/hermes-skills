# HTML 模板内嵌 JS 花括号不匹配导致脚本静默不加载 — 排障记录

## 现象

点击按钮无反应，后端未收到请求，F12 控制台无任何 JS 报错。

## 根因

`<script>` 标签内 `{`/`}` 不匹配（116 开 / 117 闭），浏览器拒绝执行整个脚本块。

## 典型场景

Flask Jinja2 模板中内嵌大量 JS，删除 `if/else` 分支时残留了多余的 `}`。

## 排查步骤

1. 在浏览器 Console 执行 `typeof functionName` 确认函数是否为 `undefined`
2. 用 Python 校验文件中的 `{`/`}` 数量
3. 逐行扫描找到多余的括号
4. 确认后 Ctrl+F5 强制刷新

## 涉及文件

- `src/templates/x_interface.html` (ETSI-ASN1-Assistant V4)

## 相关提交

| 提交 | 内容 |
|------|------|
| `f1d31fb` | 删除 HTML 导出按钮（埋下 bug） |
| `c9ce7be` | 误修 1: querySelector |
| `687aba1` | **真正修复**: 删除多余花括号 |
