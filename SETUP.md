# Contract Forge - 环境配置指南

## 🚀 快速开始

### 1. 创建环境变量文件

复制 `.env.example` 文件并重命名为 `.env`：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

或者手动创建 `.env` 文件，内容如下：

```env
# Contract Forge - 环境变量配置
# ⚠️ 重要：此文件包含敏感信息，不要提交到 Git 仓库

# ============================================
# 数据库配置 - PostgreSQL
# ============================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=contract_forge
POSTGRES_USER=admin
POSTGRES_PASSWORD=contract123

# ============================================
# 缓存配置 - Redis
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ============================================
# 应用配置
# ============================================
# 环境类型：development, production, testing
ENVIRONMENT=development

# 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# API 服务
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# ============================================
# 安全配置
# ============================================
# JWT 密钥（生产环境请使用复杂的随机字符串）
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ============================================
# 外部服务配置（可选）
# ============================================
# N8N 工作流引擎
N8N_HOST=localhost
N8N_PORT=5678
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# AI 服务（如果需要）
# OPENAI_API_KEY=
# OPENAI_API_BASE=
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动数据库服务

```bash
docker-compose up -d
```

### 4. 测试连接

```bash
python database/test_connection.py
```

---

## 📋 配置说明

### 环境变量优先级

1. `.env` 文件中的配置
2. 系统环境变量
3. `config.py` 中的默认值

### 安全最佳实践

✅ **应该做的：**
- 将 `.env` 文件添加到 `.gitignore`（已完成）
- 为每个环境使用不同的密码
- 生产环境使用强密码
- 定期更换密钥

❌ **不应该做的：**
- 不要将 `.env` 文件提交到 Git
- 不要在代码中硬编码密码
- 不要在开发和生产环境使用相同密码
- 不要分享 `.env` 文件

### 生产环境配置

在生产环境部署时，请修改以下配置：

```env
# 设置为生产环境
ENVIRONMENT=production

# 使用强密码
POSTGRES_PASSWORD=your_very_strong_password_here

# 使用复杂的 JWT 密钥（建议 32+ 字符随机字符串）
SECRET_KEY=use_python_secrets_token_urlsafe_32_to_generate

# 关闭调试模式
API_DEBUG=False
```

生成安全的密钥：

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## 🔧 使用配置模块

### 在代码中使用配置

```python
from config import Config

# 获取数据库配置
db_config = Config.get_database_config()

# 获取 Redis 配置
redis_config = Config.get_redis_config()

# 判断环境
if Config.is_production():
    # 生产环境逻辑
    pass
elif Config.is_development():
    # 开发环境逻辑
    pass
```

### 验证配置

```bash
python config.py
```

这将打印当前配置并验证是否存在问题。

---

## 🐳 Docker Compose 环境变量

`docker-compose.yml` 现在会自动从 `.env` 文件读取配置：

```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?请在 .env 文件中设置 POSTGRES_PASSWORD}
```

如果未设置必需的环境变量，Docker Compose 会报错并提示。

---

## 🔍 故障排查

### 问题：找不到 .env 文件

**解决方案：**
1. 确认 `.env` 文件在项目根目录
2. 检查文件名是否正确（不是 `.env.txt`）

### 问题：数据库连接失败

**解决方案：**
1. 确认 Docker 容器正在运行：`docker-compose ps`
2. 检查 `.env` 中的数据库配置是否正确
3. 确认端口未被占用

### 问题：配置验证失败

**解决方案：**
运行 `python config.py` 查看具体错误信息

---

## 📚 相关文件

- `.env` - 实际配置文件（不提交到 Git）
- `.env.example` - 配置模板文件
- `config.py` - 配置管理模块
- `docker-compose.yml` - Docker 服务配置
- `.gitignore` - 已包含 `.env` 排除规则

---

## ⚡ 快速参考

### 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务（应用新的环境变量）
docker-compose restart

# 测试数据库连接
python database/test_connection.py

# 验证配置
python config.py
```

---

## 🎯 下一步

配置完成后，你可以：

1. ✅ 开发后端 API 服务
2. ✅ 启动前端项目
3. ✅ 创建第一个工作流
4. ✅ 部署到生产环境

需要帮助？查看项目文档或提交 Issue。

