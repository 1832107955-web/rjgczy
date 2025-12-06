# Hotel AC Simulation (Django)

这个仓库包含一个用于课程作业的分布式温控系统（基于 Django）的演示项目，内含前端模板、后端逻辑、以及用于生成设计文档图表的脚本。

快速开始（本地开发）

1. 创建并激活虚拟环境
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖
```powershell
pip install -r requirements.txt
```

3. 运行数据库迁移并启动开发服务器
```powershell
python manage.py migrate
python manage.py runserver
```

4. 打开浏览器访问 `http://127.0.0.1:8000/`

将项目推送到 GitHub（团队协作）

方法 A（推荐 — 使用 GitHub CLI `gh`）:
```powershell
# 登录 gh: gh auth login
gh repo create <your-org-or-username>/<repo-name> --public --source=. --remote=origin --push
```

方法 B（网页方式）:
1. 在 https://github.com/new 创建新仓库。
2. 在本地运行下面命令把项目推送到远程（替换为你的 repo URL）：
```powershell
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

协作说明

- GitHub 支持多人协作：通过分支、Pull Request、代码评审、Issues 与 Actions 可以很好地支持小组协作和任务分配。
- 推荐使用 feature 分支和 Pull Request 流程：每个人在自己的分支开发，然后发起 PR 给 `main`，通过 review 后合并。

安全与注意

- 请不要把 `SECRET_KEY`、密码或生产配置上传到公共仓库。可使用环境变量或 `.env` 文件（并将 `.env` 添加到 `.gitignore`）。
# 酒店分布式温控系统（Django）

本项目使用 Django 实现了一个酒店中央空调的模拟与调度系统，采用分层架构以凸显 Django 的工程化实践：

## 架构概览
- `core/`：业务应用（Single app，清晰分层）
  - `models.py`：领域模型（`Room`, `Bill`）
  - `views.py`：Web 层（页面与 API），使用 `login_required` 保护需要登录的页面
  - `urls.py`：路由，设置了 `app_name = 'core'`
  - `templates/core/`：模板目录
    - `base.html`：基础布局模板
    - 其他页面通过 `{% extends 'core/base.html' %}` 继承
  - `static/core/`：静态资源（css/js）
  - `services/`：领域服务层
    - `config.py`：系统配置与常量
    - `scheduler.py`：调度器（优先级+时间片轮转+抢占）
    - `simulation.py`：仿真引擎（温度变化与计费模拟）
  - `management/commands/start_simulation.py`：管理命令，可独立启动调度与仿真线程
  - `apps.py`：在 `ready()` 中启动初始化、调度与仿真（带 `RUN_MAIN` 保护）

> 说明：`core/logic/` 已被 `core/services/` 取代（为了更贴合 Django/DDD 的“服务层”表达）。如无需要，可手动删除 `core/logic/` 目录。

## 运行与登录
- 数据库迁移：
```powershell
python manage.py migrate
```
- 创建管理员（若未创建）：
```powershell
python manage.py createsuperuser
```
- 启动服务：
```powershell
python manage.py runserver
```
- 登录：访问根路径 `/`，使用管理员账号登录后进入仪表盘。

## 可选：单独启动仿真
如果不通过 `apps.ready()` 自动启动，也可以手动执行：
```powershell
python manage.py start_simulation
```

## 路由说明
- `/` 登录页（未登录跳此）
- `/dashboard/` 仪表盘（登录后首页）
- `/monitor/` 监控中心
- `/reception/` 前台
- `/customer/<room_id>/` 客房控制
- `/admin/` Django 后台
- API：`/api/rooms/`, `/api/room/<id>/`, `/api/control/<id>/`, `/api/checkin/`, `/api/checkout/`

## 设计要点
- 使用基础模板统一样式与导航，减少重复
- 静态资源集中管理，页面仅引入需要的 js/css
- 服务层与 Web 层解耦，便于测试与扩展
# rjgczy
hahahahhahhahahhahahahh
