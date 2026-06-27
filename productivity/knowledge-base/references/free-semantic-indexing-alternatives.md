# 免费/本地语义索引替代方案

> 比较 enzyme（付费）的免费替代品，2026-06-26 更新

## 背景

`enzyme` (enzyme.garden) 是一个基于"催化剂+向量"的付费语义搜索引擎（v0.5.15）。2026-06-11 迁移到 `kb-search.py`（FTS5 + SiliconFlow 嵌入），2026-06-26 又新增了全本地方案 `kb-index`（TF-IDF + LSA），并彻底删除了 enzyme（二进制、插件、配置、缓存）。

## 当前系统方案：kb-index（推荐）

`kb-index` 位于 `~/.local/bin/kb-index`，基于 scikit-learn 的 TF-IDF + LSA（潜在语义分析），**完全本地运行，零网络依赖**。

```bash
# 在 Hermes venv 中激活
source ~/.hermes/venv/bin/activate

kb-index index --full    # 全量重建（首次约 3 分钟，1762 文件）
kb-index                 # 增量刷新（2~3 秒）
kb-index search "查询词"  # 语义搜索
kb-index status          # 索引状态
```

当前索引：1762 文件，949191 片段，TF-IDF 50000 特征 → LSA 256 维（方差保留 43.8%）。

**优点：**
- 完全免费、完全本地、零 API 调用
- TF-IDF + LSA 对技术文档（LI/通信协议）效果良好
- 增量刷新仅 2~3 秒
- 模型缓存 `~/.cache/kb-index/`（~2.2GB）

**缺点：**
- 纯词频语义，不如 BERT 嵌入对同义词/跨语言好
- 中文分词依赖 scikit-learn 的 `(?u)\b\w+\b` 模式（逐字 token），对中文术语匹配有局限

**安装/更新：**
直接编辑 `~/.local/bin/kb-index` 即可。依赖 `scikit-learn`, `numpy`, `scipy`（在 Hermes venv 中）。
如需补充依赖（国内镜像）：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple scikit-learn
```

## 方案对比

| 方案 | 安装 | 后端 | 搜索方式 | 离线 | 适合场景 |
|------|------|------|----------|:----:|----------|
| **kb-index** ← 当前在用 | `~/.local/bin/kb-index`（已有） | scikit-learn TF-IDF + LSA | 语义搜索 / 余弦相似度 | ✅ 全离线 | 本地知识库 ~2000 文件 |
| **kb-search.py** ← 仍在用 | 已有脚本 | SQLite FTS5 + SiliconFlow API | 全文搜索 + 语义嵌入混合 | 半（嵌入需API） | FTS5 全文搜索 |
| **txtai** | `pip install txtai`（~2GB 含 torch） | SQLite + HNSW 向量 | 语义搜索 / QA / 相似度 | ✅ 可全离线 | 需要 BERT 级语义时 |
| **ChromaDB + sentence-transformers** | `pip install chromadb sentence-transformers` | Chroma 向量数据库 | 语义搜索 / 按内容检索 | ✅ 可全离线 | 灵活配置，数据可迁移 |
| **FAISS + sentence-transformers** | `pip install faiss-cpu sentence-transformers` | FAISS 索引文件 | 近似最近邻搜索 | ✅ 可全离线 | 大规模（>10万文档）高性能搜索 |
| **LlamaIndex** | `pip install llama-index` | 支持 Chroma/FAISS/Qdrant 等 | RAG 管道 + 语义搜索 | ✅ 可全离线 | 需要 RAG 完整链路时 |

## 其他方案详解

### 方案 A：txtai（BERT 级语义，需 torch）

txtai 由 NeuML 开发，全栈语义搜索平台。但需要 torch + 约 2GB CUDA 包。

```bash
# 国内镜像安装（避开 nvidia CUDA 包）
pip install --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple torch
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple txtai
```

### 方案 B：ChromaDB + sentence-transformers

轻量级向量数据库，需 torch。安装方式同上 torch 技巧。

## 国内 pip 安装技巧（关键）

在 rhino01（中国网络环境）下安装大 Python 包时：

1. **使用清华镜像**：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <包名>`
2. **torch 先 --no-deps 绕过 NVIDIA CUDA 包**：
   ```bash
   pip install --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple torch
   ```
   这样只下载 torch 本身（~532MB），不下载 nvidia-cublas/cudnn/cusolver 等 2GB+ 的 CUDA 包。
3. **然后用 sentence-transformers/txtai 的 pip install** 会自动 pick 已有的 torch，不会再拉 CUDA 包。

**注意**：如果 torch 的 `--no-deps` 安装后 `sentence-transformers` 尝试拉 CUDA 包，是因为 torch 的 metadata 声明了这些依赖。实际运行只需要 torch 本身，不需要 CUDA 包。

## 本机环境

- rhino01, 16GB RAM, AMD CPU, 无 GPU
- 知识库 ~1762 文件（.md/.txt），索引约 2.2GB
- kb-search.py 的 FTS5 索引约 73MB
- kb-index 的 TF-IDF+LSA 模型约 2.2GB
- 256 维 LSA 降维，内存占用约 400MB（加载模型时）
