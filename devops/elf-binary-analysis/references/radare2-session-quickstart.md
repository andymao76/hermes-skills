# radare2 分析 .so 文件的典型会话示例

## 推荐分析流程总结

```bash
r2 -e bin.cache=true /home/andymao/x/ztlig/libhwx1.so
aaa       # 全量分析函数、引用
aap       # 查找函数前导
afl       # 确认函数存在
```

跳转时使用函数入口地址（不要带 dbg. 前缀）：
```r2
s 0x0002f58a     # 切换函数入口
pdf              # 打印函数汇编
pdc              # 打印伪 C 代码
```

## 输出到文件

```r2
afl > functions.txt   # 函数列表
pdc > func.c          # 当前函数 C 代码
izz > strings.txt     # 字符串表
is > symbols.txt      # 符号表
```

## 注意事项

- 确认分析完成：`aaa`（非 `aa`）保证全量分析
- 跳转用裸地址：`s 0xaddr`，不用 `s dbg.xxx`
- 反编译需要 r2dec 插件：`r2pm -i r2dec`
- .so 文件不可动态调试（无入口执行点），仅可静态分析
