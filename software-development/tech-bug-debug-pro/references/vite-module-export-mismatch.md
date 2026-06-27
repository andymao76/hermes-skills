# Vite / JS 模块导出名不匹配调试

## 场景

页面空白，浏览器 Console 报错：

```
Uncaught SyntaxError: The requested module '...' does not provide an export named 'XXX'
```

## 排查步骤

### 1. 确认模块版本

```bash
cat node_modules/<package>/package.json | grep '"version"'
```

### 2. 检查实际导出名

```bash
# 查看 dist 文件的 export 语句（ESM 包）
tail -20 node_modules/<package>/dist/<main-file>.js | grep export

# 或直接搜索
grep "export {" node_modules/<package>/dist/<main-file>.js
```

### 3. 对比文档/迁移指南

版本升级可能导致导出名变更。常见模式：

| 包 | v1 → v2 变更 |
|----|-------------|
| react-window | `FixedSizeList` → `List`，`FixedSizeGrid` → `Grid` |
| @uiw/react-json-view | 导出路径变化 |

### 4. 修复

```diff
- import { FixedSizeList as List } from 'react-window';
+ import { List } from 'react-window';
```

### 5. 清除 Vite 缓存并重启

```bash
rm -rf node_modules/.vite
npm run dev
# 浏览器 Ctrl+F5 硬刷新
```

## 常见模式

- 组件库从 v1 到 v2 常常简化命名（去掉 Fixed/Variable 前缀）
- 命名导出 → 默认导出变更
- 子路径导出 → 主入口导出变更

## 关键命令速查

```bash
# 检查版本
cat node_modules/<pkg>/package.json | grep version

# 检查 ESM 导出
tail -30 node_modules/<pkg>/dist/<main>.js | grep "export {"

# 清除 Vite 预构建缓存
rm -rf node_modules/.vite

# 硬刷新浏览器（跳过缓存）
Ctrl + Shift + R  或  Ctrl + F5
```
