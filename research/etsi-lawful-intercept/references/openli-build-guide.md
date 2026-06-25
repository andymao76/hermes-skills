# OpenLI 开源 ETSI LI 系统 — 编译部署指南

> 仓库: https://github.com/OpenLI-NZ/openli (GPL-3.0)
> 版本: v1.1.19
> 语言: C (99.2%)
> 维护: SearchLight Ltd, New Zealand

## 架构

| 组件 | 角色 | 关键依赖 |
|------|------|----------|
| **Provisioner** | 中央控制器，REST API 管理拦截任务 | libmicrohttpd, libjson-c, libsqlcipher |
| **Collector** | 抓包、识别目标流量、ETSI 编码 | libtrace, libosip2(SIP), DPDK 可选 |
| **Mediator** | 汇聚合话、HI2/HI3 交付执法机构 | RabbitMQ, libzmq |

## 完整编译流程

### 1. 系统依赖

```bash
sudo apt-get install -y libyaml-dev libosip2-dev uthash-dev libzmq3-dev \
  libjudy-dev libmicrohttpd-dev libjson-c-dev libsqlcipher-dev \
  librabbitmq-dev libb64-dev libgoogle-perftools-dev uuid-dev \
  libtrace3-dev autoconf automake libtool pkg-config
```

### 2. WAND 专有库（按依赖顺序编译）

WAND (Waikato University) 三个底层库必须手动编译安装：

```bash
# 2.1 libwandder — ASN.1 DER/PER 编解码
cd ~/projects
git clone https://github.com/LibtraceTeam/libwandder.git
cd libwandder
./bootstrap.sh
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install
sudo ldconfig

# 2.2 libwandio — I/O 抽象层
cd ~/projects
git clone https://github.com/LibtraceTeam/wandio.git
cd wandio
./bootstrap.sh
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install
sudo ldconfig

# 2.3 libtrace — 网络包捕获/处理（需 libwandio + libpcap-dev + bison + flex）
sudo apt-get install -y libpcap-dev bison flex
cd ~/projects
git clone https://github.com/LibtraceTeam/libtrace.git
cd libtrace
./bootstrap.sh
./configure --prefix=/usr/local LDFLAGS="-L/usr/local/lib" CPPFLAGS="-I/usr/local/include"
make -j$(nproc)
sudo make install
sudo ldconfig
```

### 3. 编译 OpenLI

```bash
cd ~/projects/openli
./bootstrap.sh
./configure --prefix=/usr/local LDFLAGS="-L/usr/local/lib -Wl,-rpath,/usr/local/lib" CPPFLAGS="-I/usr/local/include"
make -j$(nproc)
sudo make install
```

### 4. 验证

```bash
openli-provisioner --version
openli-collector --version
openli-mediator --version
```

## 注意事项

- **编译顺序不可变**: libwandder → libwandio → libtrace → OpenLI（下层库编不过上层就编不了）
- **pkg-config 缺失**: libwandder/libtrace 没有 `.pc` 文件，必须用 `LDFLAGS`/`CPPFLAGS` 显式指定路径
- **libtrace 版本**: Ubuntu apt 源的 libtrace3-dev (3.x) 不够，必须从 GitHub 编 ≥4.0.27
- **libtrace configure.in**: 文件名是 `configure.in` 不是 `configure.ac`，bootstrap 会自动处理
- **运行要求**: Mediator 需要 RabbitMQ 服务运行中
- **DPDK**: Collector 可选 DPDK 加速，编译时需额外配置
- **Chrome 打开本地 HTML**: 使用 `google-chrome --new-window /path/to/file.html`

## 相关链接

- OpenLI 官方: https://github.com/OpenLI-NZ/openli
- OpenLI Wiki: https://github.com/OpenLI-NZ/openli/wiki
- WAND 研究组: https://www.wand.net.nz/
- 本地克隆: `~/projects/openli/`
