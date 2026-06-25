BER-TLV TAG 解码分析工具 — 三种 TAG 长度假设（2位/4位/6位）

用法：
  python3 ber-tag-analyzer.py "30 2D 80 08 64 10..."
  python3 ber-tag-analyzer.py --mode bytewise --step 20 "9F 1F 81..."
  python3 ber-tag-analyzer.py --interactive

结构模式：自动按 BER TLV 结构跳转
逐字节模式：固定步进遍历
交互模式：输入码流后选模式

路径：/home/andymao/ber-tag-analyzer.py
