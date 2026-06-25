# IDA Pro MCP Server 参考

**来源**: 腾讯云开发者社区 (2026-06-14)
**适用场景**: AI辅助逆向工程、协议分析、二进制文件分析

## 概述

IDA Pro MCP Server 让 AI（Claude/LLM）直接操控 IDA Pro 进行逆向工程，支持：
- 反编译/反汇编
- 函数重命名和注释
- 交叉引用分析
- 调试（需 --unsafe 标志）

## 安装

```bash
pip install --upgrade git+https://github.com/mrexodia/ida-pro-mcp
ida-pro-mcp --install
```

## 核心工具（25+）

### 信息查询
- `get_metadata` - 获取二进制文件元数据
- `get_function_by_name/address` - 按名称/地址查函数
- `decompile_function` - 反编译指定函数
- `disassemble_function` - 反汇编指定函数
- `list_functions/globals/strings` - 列出函数/全局变量/字符串
- `get_xrefs_to` - 交叉引用分析
- `get_entry_points` - 获取入口点

### 修改操作
- `set_comment` - 添加注释
- `rename_local/global_variable` - 重命名变量
- `rename_function` - 重命名函数
- `set_function_prototype` - 设置函数原型
- `declare_c_type` - 声明C类型

### 调试（需 --unsafe）
- `dbg_set_breakpoint` - 设断点
- `dbg_run_to` - 运行到指定地址
- `dbg_get_registers/call_stack` - 读取寄存器/调用栈

## 运行模式

1. **标准 MCP (stdio)**: 本地使用
2. **SSE 传输**: `uv run ida-pro-mcp --transport http://127.0.0.1:8744/sse`
3. **无头模式**: 通过 idalib，不需要 IDA GUI

## 用户环境备注

- **用户无 IDA Pro** (商业软件，$1800+起)
- **替代方案**:
  - Ghidra (免费，NSA开源) - 功能接近 IDA
  - radare2/rizin (免费开源) - 命令行逆向
  - Wireshark + Lua 插件 - 协议层面够用

## 与 LI Decoder 项目的关联

用户的 LI Decoder 项目涉及 HI2 接口 / ASN.1 编解码 / Wireshark 协议分析。
如果未来需要分析未知二进制协议，可考虑：
1. 先用 Wireshark + Lua 插件（当前方案）
2. 需要完整逆向时，用 Ghidra（免费替代）
3. Ghidra 也有社区 MCP Server 项目

## 参考

- GitHub: https://github.com/mrexodia/ida-pro-mcp
- 腾讯云页面: https://cloud.tencent.com/developer/mcp/server/10208
