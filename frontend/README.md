# Contract Forge Frontend

智能合同处理系统 - 前端项目

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design** - UI 组件库
- **Zustand** - 状态管理
- **React Router** - 路由
- **Axios** - HTTP 客户端
- **Socket.io** - WebSocket 实时通信
- **React Flow** - 流程图可视化
- **React Dropzone** - 文件上传

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:3000

### 3. 构建生产版本

```bash
npm run build
```

## 项目结构

```
src/
├── components/          # 组件
│   ├── Layout/         # 布局组件
│   ├── ContractUpload/ # 合同上传
│   └── ContractList/   # 合同列表
│
├── pages/              # 页面
│   ├── Dashboard/      # 工作台
│   ├── ContractDetail/ # 合同详情
│   └── History/        # 历史记录
│
├── store/              # Zustand 状态管理
│   └── contractStore.ts
│
├── services/           # API 服务
│   ├── api.ts
│   └── contractService.ts
│
├── hooks/              # 自定义 Hooks
│   └── useWebSocket.ts
│
├── types/              # TypeScript 类型
│   └── contract.ts
│
├── App.tsx            # 根组件
└── main.tsx           # 入口文件
```

## 学习资源

### React + TypeScript
- [React 官方文档](https://react.dev/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)

### Ant Design
- [Ant Design 官方文档](https://ant.design/)
- [组件库](https://ant.design/components/overview-cn)

### Zustand
- [Zustand 文档](https://docs.pmnd.rs/zustand/getting-started/introduction)
- 简单易用的状态管理库

### Socket.io
- [Socket.io 客户端文档](https://socket.io/docs/v4/client-api/)
- 实时通信

## 开发指南

### 1. 添加新页面

1. 在 `src/pages/` 创建新文件夹
2. 创建 `index.tsx`
3. 在 `App.tsx` 添加路由

### 2. 添加新组件

1. 在 `src/components/` 创建新文件夹
2. 创建 `index.tsx` 和 `styles.css`
3. 在需要的地方导入使用

### 3. 状态管理

使用 Zustand 管理全局状态：

```typescript
// 创建 store
const useStore = create((set) => ({
  data: [],
  addData: (item) => set((state) => ({ 
    data: [...state.data, item] 
  })),
}))

// 在组件中使用
const { data, addData } = useStore()
```

### 4. API 调用

在 `src/services/` 中定义 API 服务：

```typescript
export const myService = {
  getData: () => api.get('/data'),
  postData: (data) => api.post('/data', data),
}
```

## 后续开发建议

1. ✅ 先运行起来，熟悉项目结构
2. ✅ 学习 Ant Design 组件使用
3. ✅ 理解 Zustand 状态管理
4. ✅ 实现文件上传功能
5. ✅ 添加 WebSocket 实时更新
6. ✅ 完善 UI 样式
7. ✅ 添加错误处理
8. ✅ 优化用户体验

## 注意事项

- 确保后端服务运行在 `http://localhost:8001`
- WebSocket 服务运行在 `http://localhost:8000`
- 开发时会自动代理 `/api` 请求到后端

## 常见问题

### 1. 端口被占用

修改 `vite.config.ts` 中的 `server.port`

### 2. 后端连接失败

检查后端服务是否启动，确认端口是否正确

### 3. 依赖安装失败

尝试清除缓存：
```bash
rm -rf node_modules package-lock.json
npm install
```

