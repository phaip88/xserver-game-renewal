# Deno Deploy 部署指南

## 修复的问题

✅ **标准库版本** - 使用固定版本 `@0.208.0` 而不是无版本导入
✅ **配置文件** - 添加了 `deno.json` 和 `deploy.json`
✅ **入口点** - 明确指定 `xhttp.ts` 作为入口点
✅ **依赖管理** - 添加了导入映射
✅ **部署忽略** - 创建了 `.deployignore` 排除不必要的文件

## 部署步骤

### 方法 1: Deno Deploy (推荐)

1. 访问 https://dash.deno.com/
2. 创建新项目
3. 连接 GitHub 仓库或直接上传文件
4. 确保入口点设置为 `xhttp.ts`
5. 设置环境变量（可选）：
   - `UUID`: 你的 UUID
   - `DOMAIN`: 你的域名
   - `XPATH`: 路径名称
   - `SUB_PATH`: 订阅路径
   - `NAME`: 服务名称

### 方法 2: 本地测试

```bash
# 安装 Deno
curl -fsSL https://deno.land/install.sh | sh

# 运行服务器
deno task start

# 或者直接运行
deno run --allow-net --allow-env --allow-read xhttp.ts
```

### 方法 3: Docker 部署

```dockerfile
FROM denoland/deno:latest

WORKDIR /app

COPY deno.json .
COPY xhttp.ts .

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-read", "xhttp.ts"]
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UUID` | `f9a1ba12-7187-4b25-a5d5-7bafd82ffb4d` | VLESS UUID |
| `PORT` | `3000` | 服务器端口 |
| `DOMAIN` | `nxhack.deno.dev` | 域名 |
| `XPATH` | `xhttp` | 代理路径 |
| `SUB_PATH` | `sub` | 订阅路径 |
| `NAME` | `Deno` | 服务名称 |

## 测试端点

部署成功后，测试以下端点：

```bash
# 健康检查
curl https://your-domain.com/health

# 根路径
curl https://your-domain.com/

# 订阅信息
curl https://your-domain.com/sub
```

## 故障排除

### 构建失败
- 确保 `xhttp.ts` 文件没有语法错误
- 检查导入语句使用了正确的版本号
- 验证 `deno.json` 格式正确

### 运行时错误
- 检查环境变量是否正确设置
- 查看部署日志中的错误信息
- 确保所有必需的权限已授予（`--allow-net`, `--allow-env`）

### 403 错误
- 已修复：添加了 User-Agent 头和备用 API
- ISP 检测失败会自动降级到 "Unknown-ISP"

## 文件说明

- `xhttp.ts` - 主服务器文件
- `deno.json` - Deno 配置和任务定义
- `deploy.json` - 部署配置
- `.deployignore` - 部署时忽略的文件
