# 服务器测试指南

## 已优化的改进

✅ **移除所有外部 API 调用** - 启动时不再调用任何外部服务
✅ **简化 ISP 检测** - 直接使用环境变量或默认值
✅ **简化 IP 检测** - 直接使用 DOMAIN 配置
✅ **优化根路径** - 返回简单的 "OK" 响应
✅ **添加健康检查** - `/health` 和 `/healthz` 端点

## 为什么 Warm up 可能失败

1. **启动超时** - 平台健康检查超时（通常 30 秒）
2. **端口问题** - 平台期望的端口与配置不匹配
3. **路径问题** - 健康检查访问了错误的路径
4. **响应格式** - 平台期望特定的响应格式

## 测试端点

部署后测试这些端点：

```bash
# 根路径（最简单的健康检查）
curl https://lucky9.deno.dev/

# 健康检查端点
curl https://lucky9.deno.dev/health

# 订阅路径
curl https://lucky9.deno.dev/zmm
```

## 预期响应

### GET /
```
OK
```

### GET /health
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "port": 3000
}
```

### GET /zmm
```
dmxlc3M6Ly9iNTllYjRiNS00ZWEwLTQ0ZjMtOGVhOS1mZDdmMDdmZmYyOGZAbHVja3k5LmRlbm8uZGV2OjQ0Mz9lbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1sdWNreTkuZGVuby5kZXYmZnA9Y2hyb21lJmFsbG93SW5zZWN1cmU9MSZ0eXBlPXhodHRwJmhvc3Q9bHVja3k5LmRlbm8uZGV2JnBhdGg9JTJGeGh0dHAmbW9kZT1wYWNrZXQtdXAjRGVuby1EZW5vLURlcGxveQ==
```

## 如果仍然失败

检查部署平台的配置：

1. **入口点** - 确保设置为 `xhttp.ts`
2. **端口** - 确认平台使用的端口（可能需要设置 PORT 环境变量）
3. **健康检查路径** - 在平台设置中指定 `/` 或 `/health`
4. **启动命令** - 应该是 `deno run --allow-net --allow-env xhttp.ts`

## 环境变量

确保在部署平台设置了：

```
DOMAIN=lucky9.deno.dev
UUID=b59eb4b5-4ea0-44f3-8ea9-fd7f07fff28f
SUB_PATH=zmm
XPATH=xhttp
NAME=Deno
ISP=Deno-Deploy
```

## 快速诊断

如果服务器启动但 Warm up 失败，可能是：
- 健康检查路径配置错误
- 健康检查超时设置太短
- 平台期望特定的响应头或状态码

建议在平台设置中：
- 健康检查路径：`/`
- 健康检查超时：60 秒
- 预期状态码：200
