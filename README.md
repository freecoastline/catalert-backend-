# CatAlert Backend

CatAlert后端服务，集成AI Agent能力，为iOS应用提供智能猫咪护理管理功能。

## 功能特性

### 核心功能
- 🐱 猫咪档案管理
- ⏰ 智能提醒系统
- 📊 活动记录跟踪
- 🤖 AI健康分析
- 📈 行为模式识别
- 💡 个性化建议

### AI Agent能力
- 智能健康监测
- 行为模式分析
- 提醒时间优化
- 异常检测预警
- 自然语言交互
- 个性化推荐

## 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL + Redis
- **AI服务**: OpenAI GPT-4 + 本地ML模型
- **认证**: JWT + OAuth2
- **部署**: Docker + Docker Compose
- **监控**: Prometheus + Grafana

## 项目结构

```
catalert-backend/
├── app/
│   ├── api/                 # API路由
│   ├── core/               # 核心配置
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic模式
│   ├── services/           # 业务逻辑
│   ├── ai/                 # AI Agent相关
│   └── utils/              # 工具函数
├── tests/                  # 测试文件
├── docker/                 # Docker配置
├── docs/                   # API文档
└── requirements.txt        # 依赖包
```

## 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker (可选)

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd catalert-backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥
```

5. 初始化数据库
```bash
alembic upgrade head
```

6. 启动服务
```bash
uvicorn app.main:app --reload
```

### Docker部署

```bash
docker-compose up -d
```

## API文档

启动服务后访问: http://localhost:8000/docs

## 开发指南

### 添加新的API端点
1. 在 `app/api/` 中创建路由文件
2. 在 `app/schemas/` 中定义请求/响应模式
3. 在 `app/services/` 中实现业务逻辑
4. 更新API文档

### AI Agent开发
1. 在 `app/ai/` 中添加新的Agent功能
2. 在 `app/services/` 中集成AI服务
3. 添加相应的测试用例

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License
