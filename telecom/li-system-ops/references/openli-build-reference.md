# OpenLI — 开源 ETSI LI 系统构建与测试参考

> GitHub: https://github.com/OpenLI-NZ/openli
> 版本: v1.1.19 (2026-06-14)
> 许可证: GPL-3.0
> 语言: C (99.2%)

---

## 系统架构

| 组件 | 角色 | 依赖 |
|------|------|------|
| **Provisioner** | 中央控制器，REST API 管理设控 | libmicrohttpd, libjson-c, libsqlcipher |
| **Collector** | 抓包、识别目标流量、ETSI 编码输出 | libtrace, libosip2(SIP), DPDK 可选 |
| **Mediator** | 汇聚合话、HI2/HI3 交付执法机构 | RabbitMQ, libzmq |

## 完整依赖链

```
wandio (v6.0.6) → libtrace (v7.2.4) → OpenLI (v1.1.19)
                                       ↗ libwandder (v2.4.5)
```

## 构建步骤

### 1. 系统依赖

```bash
sudo apt-get install -y autoconf automake libtool pkg-config \
  libyaml-dev libosip2-dev uthash-dev libzmq3-dev libjudy-dev \
  libmicrohttpd-dev libjson-c-dev libsqlcipher-dev librabbitmq-dev \
  libb64-dev libgoogle-perftools-dev uuid-dev libpcap-dev bison flex
```

### 2. 编译 wandio

```bash
git clone https://github.com/LibtraceTeam/wandio.git
cd wandio
./bootstrap.sh
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install && sudo ldconfig
```

### 3. 编译 libtrace

```bash
git clone https://github.com/LibtraceTeam/libtrace.git
cd libtrace
# libtrace 使用 configure.in, configure 已预生成
./configure --prefix=/usr/local \
  LDFLAGS="-L/usr/local/lib -Wl,-rpath,/usr/local/lib" \
  CPPFLAGS="-I/usr/local/include"
make -j$(nproc)
sudo make install && sudo ldconfig
```

### 4. 编译 libwandder

```bash
git clone https://github.com/LibtraceTeam/libwandder.git
cd libwandder
./bootstrap.sh
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install && sudo ldconfig
```

### 5. 编译 OpenLI

```bash
git clone https://github.com/OpenLI-NZ/openli.git
cd openli
./bootstrap.sh
./configure LDFLAGS="-L/usr/local/lib -Wl,-rpath,/usr/local/lib" \
  CPPFLAGS="-I/usr/local/include"
make -j$(nproc)
```

### 6. 验证

```bash
# 三个二进制文件
src/openliprovisioner -h
src/openlicollector -h
src/openlimediator -h
```

## 测试运行

### 最小配置示例

```yaml
# /tmp/openli-prov.yaml
clientaddr: 127.0.0.1
clientport: 9001
mediationaddr: 127.0.0.1
mediationport: 12001
updateaddr: 127.0.0.1
updateport: 9009
intercept-config-file: /tmp/openli-intercept.yaml
encrypt-intercept-config-file: no
```

```yaml
# /tmp/openli-coll.yaml
provisioneraddr: 127.0.0.1
provisionerport: 9001
operatorid: TEST
networkelementid: test01
interceptpointid: coll01
seqtrackerthreads: 1
encoderthreads: 2
forwardingthreads: 1
gtpthreads: 0
sipthreads: 1
emailthreads: 0
```

### 启动顺序

```bash
# 终端1: 先启动 provisioner
~/projects/openli/src/openliprovisioner -c /tmp/openli-prov.yaml

# 终端2: 再启动 collector
~/projects/openli/src/openlicollector -c /tmp/openli-coll.yaml
```

## VS Code 集成配置

配置文件写入 `.vscode/` 目录：

| 文件 | 功能 |
|------|------|
| `c_cpp_properties.json` | C 智能感知 (includePath + /usr/local/include) |
| `tasks.json` | 编译任务 (build/configure/full rebuild) |
| `launch.json` | 调试配置 (collector/mediator/provisioner) |

## 经验总结

- **libtrace 需要 libwandio — 顺序不能错**: wandio → libtrace → libwandder → OpenLI
- **configure 需指定 /usr/local**: 因为 wandio/libtrace/libwandder 都安装到 /usr/local
- **libtrace 使用 configure.in** (不是 configure.ac), configure 已预生成，直接跑
- **OpenLI 不需要 sudo make install** 也能运行，从 src/ 下直接执行即可
- **libtrace 需要 bison+flex 和 libpcap-dev**，否则 configure 会报 critical packages missing
