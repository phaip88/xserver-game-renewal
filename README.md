# Xray-Sing Proxy Server

一个集成了 Xray (VLESS) 和 Sing-box (Hysteria2) 的代理服务器项目。

## 功能特性

- ✅ **Xray VLESS 协议**：通过 Cloudflare Argo Tunnel 提供服务
- ✅ **Hysteria2 协议**：基于 QUIC 的高性能代理协议
- ✅ **自动证书生成**：自动生成 TLS 自签名证书
- ✅ **Web 订阅页面**：提供友好的订阅链接管理界面
- ✅ **随机 UUID**：每次启动自动生成随机 UUID，提高安全性
- ✅ **流量伪装**：使用 SNI 伪装技术隐藏流量特征

## 快速开始

### 方法 1：从 GitHub Actions 下载构建好的 JAR

1. 进入项目的 [Actions](../../actions) 页面
2. 选择最新的成功构建
3. 下载 `server-jar` 文件
4. 或者从 [Releases](../../releases) 页面下载最新版本

### 方法 2：本地构建

#### Windows:
```bash
build.bat
```

#### Linux/Mac:
```bash
javac minecraft.java
echo "Main-Class: minecraft" > Manifest.txt
jar cvmf Manifest.txt server.jar *.class META-INF/
rm Manifest.txt *.class
```

## 运行

```bash
java -jar server.jar
```

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `UUID` | Xray VLESS UUID | 随机生成 |
| `SUB_PATH` | 订阅路径 | `zmm` |
| `PORT` | HTTP 服务器端口 | `3000` |
| `SB_PORT` | Hysteria2 端口 | `2705` |
| `SB_SNI` | Hysteria2 SNI 域名 | `time.android.com` |
| `ARGO_DOMAIN` | Argo 隧道固定域名 | 空（自动生成） |
| `ARGO_AUTH` | Argo 隧道认证 Token | 空 |
| `CFIP` | Cloudflare CDN IP/域名 | `www.kick.com` |

### 配置示例

```bash
# 设置固定 UUID
export UUID="your-custom-uuid"

# 设置自定义订阅路径
export SUB_PATH="my-secret-path"

# 设置端口
export PORT="8080"
export SB_PORT="3000"

# 运行
java -jar server.jar
```

## 访问订阅

启动后访问：`http://服务器IP:3000/zmm`

页面会显示：
- Xray VLESS 连接链接
- Hysteria2 连接链接
- Base64 订阅链接

## 安全建议

1. ✅ **修改默认订阅路径**：通过 `SUB_PATH` 环境变量设置
2. ✅ **使用随机 UUID**：项目已默认启用
3. 🔒 **添加防火墙规则**：限制订阅页面的访问 IP
4. 🔒 **使用反向代理**：通过 Nginx 添加认证
5. 🔒 **定期更换 UUID**：重启服务自动生成新 UUID

## 系统要求

- Java 17 或更高版本
- Linux 系统（推荐 Ubuntu/Debian）
- OpenSSL（用于生成证书）
- curl（用于下载组件）

## 注意事项

⚠️ **本项目仅供学习和研究使用，请遵守当地法律法规。**

## License

MIT License
