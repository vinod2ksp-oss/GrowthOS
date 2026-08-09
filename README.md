# GrowthOS 成长系统

## 项目概览

GrowthOS 面向本科生考研场景，提供用户档案、考研目标、任务管理、学习计时、成果上传与规则评测的最小闭环。

## 技术栈

- Frontend: Next.js 15 + TypeScript + Tailwind CSS + App Router
- Backend: FastAPI + SQLAlchemy 2 + Pydantic 2 + Alembic
- Database: PostgreSQL
- Storage: local file storage via `StorageService`

## 目录结构

- `frontend/`: Next.js 应用
- `backend/`: FastAPI 服务
- `docker-compose.yml`: PostgreSQL 容器

## Windows 启动命令

```powershell
cd d:\论文写作\demo\Grouth
copy backend\.env.example backend\.env
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## 前端启动命令

```powershell
cd frontend
npm install
npm run dev
```

## 迁移说明

- Alembic 默认管理迁移脚本。
- 初始化数据库为空，执行 `alembic upgrade head` 后自动创建表结构。

## 创建首个管理员

管理员不能通过公开注册接口创建。先正常注册账号并完成数据库迁移，然后在后端目录使用项目虚拟环境执行：

```powershell
& 'D:\论文写作\demo\GROUTH\.venv\Scripts\python.exe' -m app.cli.set_admin user@example.com
```

命令只会提升已存在的精确邮箱账号；资源数据库初始为空，不包含预置商品。
