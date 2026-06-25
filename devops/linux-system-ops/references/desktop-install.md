# 桌面应用与开发工具安装

适用于 Ubuntu 24.04 的 GUI 应用和开发工具安装指南，涵盖各种安装包格式。

## 工具索引

| 工具 | 安装方式 | 备注 |
|------|---------|------|
| SoapUI 5.10.0 | shell 安装器 (`-c` 控制台模式) | WSDL/SOAP 测试工具，含 CLI 套件 |

---

## SoapUI 5.10.0 安装

SoapUI 开源版最新版本可在 [GitHub Releases](https://github.com/SmartBear/soapui/releases) 或 [官网](https://www.soapui.org/downloads/latest-release/) 下载。

### 前置条件

```bash
java -version  # 需要 Java 8+，OpenJDK 21 已验证可用
```

### 下载

安装包托管在 `dl.eviware.com`，从**中国网络**下载较慢（峰值约 1MB/s，197MB 通常需 3-5 分钟，可能会被中断）：

```bash
cd /tmp
wget https://dl.eviware.com/soapuios/5.10.0/SoapUI-x64-5.10.0.sh -O SoapUI-x64-5.10.0.sh
```

如果 `dl.eviware.com` 慢，可尝试 SourceForge 镜像：
```bash
wget https://sourceforge.net/projects/soapui.mirror/files/v5.10.0/SoapUI-x64-5.10.0.sh/download -O SoapUI-x64-5.10.0.sh
```

> ⚠️ SourceForge 镜像**返回的是 HTML 重定向页而非实际文件**（53KB HTML），不是有效安装包。下载后务必检查文件类型：`file SoapUI-x64-5.10.0.sh`（应为 `POSIX shell script executable` 而非 `HTML document`）。推荐直接走 `dl.eviware.com` 配合 `wget -c` 断点续传。

**下载中断处理：** dl.eviware.com 对中国网络连接不稳定，wget 可能中途超时或中断。推荐方案：

```bash
# 方法一：后台下载 + 断点续传（推荐）
wget -c -q --show-progress "https://dl.eviware.com/soapuios/5.10.0/SoapUI-x64-5.10.0.sh" -O /tmp/SoapUI-x64-5.10.0.sh

# 如果中断，重新运行会自动从断点继续
# 完整文件约 198MB

# 方法二：curl 重连
curl -L -o /tmp/SoapUI-x64-5.10.0.sh \
  "https://dl.eviware.com/soapuios/5.10.0/SoapUI-x64-5.10.0.sh" \
  --connect-timeout 30 --speed-time 30 --speed-limit 10240 \
  --retry 5 --retry-delay 10
```

> 在 Hermes 中，因终端工具默认 timeout 180 秒，建议用 `terminal(background=true, timeout=600)` 配合 `notify_on_complete=true` 处理，避免中途超时。

### 无桌面环境安装（控制台模式）

SoapUI 使用 BitRock/install4j 安装器，传递 `-c` 启用控制台模式。通过 `printf` 管道传入安装应答：

```bash
chmod +x /tmp/SoapUI-x64-5.10.0.sh
cd /tmp && printf '\n\n\n\ny\n\nn\n\n' | /tmp/SoapUI-x64-5.10.0.sh -c
```

安装应答说明：
| 输入 | 含义 |
|------|------|
| `\n` (1) | 欢迎页 — 确认 |
| `\n` (2) | 安装路径 — 默认 `~/SmartBear/SoapUI-5.10.0` |
| `\n` (3) | 组件选择 — 全选（默认） |
| `\n` (4) | Tutorials 路径 — 默认 |
| `y\n` | 是否创建符号链接 → 是 |
| `\n` (6) | 符号链接目录 — 默认 `/usr/local/bin`（无 root 权限会失败） |
| `n\n` | 是否创建桌面图标 → 否 |

> ⚠️ `/usr/local/bin` 需要 root 权限，安装器可能静默跳过。安装后需手动创建用户级符号链接。

### 安装后验证

```bash
# 验证安装目录
ls ~/SmartBear/SoapUI-5.10.0/bin/soapui.sh
du -sh ~/SmartBear/SoapUI-5.10.0/  # 约 310MB

# 创建用户级符号链接（代替 /usr/local/bin）
mkdir -p ~/.local/bin
ln -sf ~/SmartBear/SoapUI-5.10.0/bin/soapui.sh ~/.local/bin/soapui
ln -sf ~/SmartBear/SoapUI-5.10.0/bin/testrunner.sh ~/.local/bin/testrunner
# 同样可为 mockservicerunner, loadtestrunner, securitytestrunner, wargenerator, toolrunner 创建链接
```

确保 `~/.local/bin` 在 PATH 中：

```bash
# 检查
echo $PATH | grep -o '.local/bin'
# 如果不在，编辑 ~/.bashrc 或 ~/.zshrc:
# export PATH="$HOME/.local/bin:$PATH"
```

### CLI 工具一览

| 脚本 | 用途 |
|------|------|
| `soapui.sh` | GUI 启动（需要 X11/桌面环境） |
| `testrunner.sh` | 命令行执行测试用例 |
| `mockservicerunner.sh` | 启动 Mock 服务 |
| `loadtestrunner.sh` | 压力/负载测试 |
| `securitytestrunner.sh` | 安全性测试 |
| `wargenerator.sh` | 导出为 WAR 包 |
| `toolrunner.sh` | 工具集启动器 |

### CLI 使用示例

```bash
# 运行测试（查看参数：不传参直接运行 testrunner.sh）
testrunner.sh -s"TestSuite" -c"TestCase" -r -j -freports/ my-project-soapui-project.xml

# 启动 Mock 服务
mockservicerunner.sh -p 8089 -m "file:///path/to/mock-response.xml" my-project-soapui-project.xml
```

### 创建测试项目验证安装

如需验证 SoapUI 是否工作正常，可创建一个 Mock 项目并发送 SOAP 请求验证：

**⚠️ 关键踩坑：SoapUI 项目 XML 文件必须声明 `xmlns:xsi` 命名空间**

如果项目 XML 中包含 `xsi:type` 属性（即 `xsi:type="con:WsdlTestRequestStep"`、`xsi:type="con:WsdlInterface"` 等），根元素 `<con:soapui-project>` 必须显式声明 `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"`，否则 SoapUI 报错 `The prefix "xsi" for attribute "xsi:type" is not bound` 且无法加载项目。

**验证安装的完整步骤（不依赖网络 WSDL）：**

1. 创建 Mock 项目 XML（最小有效版本 — 包含根命名空间声明）：

```xml
<con:soapui-project id="mock-test" name="Mock-Test" 
    xmlns:con="http://eviware.com/soapui/config"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <con:mockService name="HelloMock" port="9090" path="/mock" host="0.0.0.0">
    <con:mockOperation name="sayHello" interface="HelloInterface" operation="sayHello">
      <con:mockResponse name="HelloResponse" 
        responseContent="&lt;soap:Envelope xmlns:soap=&quot;http://schemas.xmlsoap.org/soap/envelope/&quot;&gt;
          &lt;soap:Body&gt;
            &lt;sayHelloResponse xmlns=&quot;http://example.com/&quot;&gt;
              &lt;greeting&gt;Hello from SoapUI Mock!&lt;/greeting&gt;
            &lt;/sayHelloResponse&gt;
          &lt;/soap:Body&gt;
        &lt;/soap:Envelope&gt;"/>
    </con:mockOperation>
  </con:mockService>
</con:soapui-project>
```

2. 启动 Mock 服务：

```bash
mockservicerunner.sh -p 9090 /tmp/test-mock.xml
```

3. 用 curl 发送 SOAP 请求验证：

```bash
curl -s -X POST http://localhost:9090/mock \
  -H "Content-Type: text/xml;charset=UTF-8" \
  -H "SOAPAction: sayHello" \
  -d '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
      <sayHello xmlns="http://example.com/"><name>World</name></sayHello>
    </soap:Body>
  </soap:Envelope>'
```

4. 验证 `testrunner` 加载项目：

```bash
testrunner.sh -r test-project.xml
```

> 注意：Mock 服务返回 SOAP Fault 通常是因为 mockOperation 缺少对应的 WSDL interface 定义，不影响验证服务本身的启动和响应能力。如需完整测试，需先导入 WSDL 到项目中。

---

### 已知问题

- **从 SourceForge 下载**：链接返回的是 HTML 页面而非直接文件，需用 `file` 命令确认实际类型
- **符号链接权限**：`/usr/local/bin` 需 root，无权限时安装器静默跳过，需手动创建 `~/.local/bin` 链接
- **GUI 无法启动**：纯服务器环境无 X11 时使用 CLI 工具替代
- **testrunner `-?` 和 `-h` 无效**：`-?` 报 `Unrecognized option`，`-h` 被当作 host 参数（需要传参）。查看帮助的正确方式：不传参直接运行 `testrunner.sh`


---

## 通用 BitRock/install4j 安装器处理

SoapUI 安装器是 BitRock/install4j 格式。此类安装器支持：

- `-c` — 控制台模式（无 GUI 可用）
- `-q` — 静默模式（自动接受默认值，不一定支持所有选项）
- 通过 `printf` 或 expect 管道应答 STDIN

典型应答序列取决于安装器版本，建议先试跑一次查看实际提示数量。
