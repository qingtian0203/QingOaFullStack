# WAP_QingOA

QingOA v1.6C WAP 流程中心，用于 App WebView 和 QingAgent 浏览器自动化联调。

## 技术栈

- Vite
- Vue 3
- TypeScript
- Vue Router hash 模式
- 自定义 CSS，不引入重 UI 库

## 启动

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/WAP_QingOA
npm install
npm run dev
```

开发服务器会把 `/api` 和 `/debug` 代理到 `http://127.0.0.1:8010`。

## 构建并由 API 托管

```bash
npm run build
```

构建产物在 `dist/`。`API_QingOA` 启动时如果检测到该目录，会挂载到：

```text
http://127.0.0.1:8010/wap/#/workflow?tab=todo
```

## Token 策略

WAP 请求层按顺序获取 token：

1. `window.QingOA.getToken()`：App WebView 注入。
2. `localStorage.qingoa_token`：浏览器调试复用。
3. WAP 内置登录表单：复用 `POST /api/auth/login`，仅用于调试和自动化。

自动化稳定选择器：

- `data-testid="wap-login-form"`
- `data-testid="wap-login-username"`
- `data-testid="wap-login-password"`
- `data-testid="wap-login-submit"`
- `data-testid="workflow-empty-returned"`
