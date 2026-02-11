# XHTTP Server - Deno 运行说明

## 关于此文件

`xhttp.ts` 是一个为 **Deno 运行时**设计的 TypeScript 文件，不是为 Node.js 设计的。

## 已修复的问题

✅ 已弃用的 `substr()` 方法 → 改为 `substring()`
✅ 未使用的变量和参数 → 使用 `_` 前缀标记
✅ 删除了未使用的 `relay` 函数
✅ 修复了正则表达式格式问题
✅ 改进了错误处理的类型安全

## 如何运行

### 1. 安装 Deno

```bash
# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex

# macOS/Linux
curl -fsSL https://deno.land/install.sh | sh
```

### 2. 运行服务器

```bash
deno run --allow-net --allow-env --allow-run xhttp.ts
```

### 3. 环境变量配置（可选）

```bash
# 设置 UUID
$env:UUID="your-uuid-here"

# 设置端口
$env:PORT="3000"

# 设置域名
$env:DOMAIN="your-domain.com"

# 设置路径
$env:XPATH="xhttp"
$env:SUB_PATH="sub"

# 设置名称
$env:NAME="MyServer"
```

## TypeScript 编译器警告

如果你在 VS Code 或其他 IDE 中看到关于 "找不到 Deno" 的错误，这是正常的。这些错误只在使用 Node.js 的 TypeScript 编译器时出现。

要在 VS Code 中获得正确的 Deno 支持：

1. 安装 Deno 扩展
2. 在项目根目录创建 `.vscode/settings.json`：

```json
{
  "deno.enable": true,
  "deno.lint": true,
  "deno.unstable": false
}
```

## 代码质量

所有代码格式和逻辑问题已修复。剩余的 TypeScript 错误仅与运行时环境有关，在 Deno 中运行时不会出现。
