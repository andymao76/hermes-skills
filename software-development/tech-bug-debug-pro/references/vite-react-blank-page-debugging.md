# Vite + React 页面空白调试指南

## 现象

Vite dev server 返回 HTTP 200，但浏览器页面空白，无 UI 渲染。

## 排查步骤（优先级排序）

### 1. 清除 Vite 预构建缓存

```bash
rm -rf node_modules/.vite
# 然后重启 dev server
```

### 2. 硬刷新浏览器

`Ctrl + Shift + R`（或 `Ctrl + F5`），不要只按 F5。

### 3. 检查浏览器 Console（F12）

最常见的空白原因为 JavaScript 运行时错误：
- `Uncaught SyntaxError: ... does not provide an export named 'X'` → 模块导出名变更
- `Uncaught TypeError: ... is not a function` → API 不兼容
- `Failed to load module script` → 依赖版本冲突

### 4. 检查依赖版本与导出

当报错提示模块导出名不存在时：

```bash
# 检查实际版本
cat node_modules/<pkg>/package.json | grep version

# 检查实际导出（ESM 模块）
tail -20 node_modules/<pkg>/dist/<module>.js | grep export

# 或搜索 src 目录
grep -r "export" node_modules/<pkg>/src/ | head -10
```

### 5. 验证 dev server 正常响应

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:5173/
curl -s http://localhost:5173/src/main.jsx | head -3
```

## 案例：react-window v2 迁移

react-window v2 将 `FixedSizeList` 更名为 `List`：

| 模式 | v1.x | v2.x |
|------|------|------|
| 导入 | `{ FixedSizeList as List }` | `{ List }` |

报错：
```
does not provide an export named 'FixedSizeList'
```

修复：删除 Vite 缓存 + 改用 `{ List }` 导入即可。

## 预防

- 升级依赖后查 CHANGELOG 或 package.json 版本
- 用 `tail -20 dist/*.js | grep export` 确认实际导出
