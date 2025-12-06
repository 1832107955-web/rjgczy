# Contributing

感谢你为此项目贡献代码！为了让小组协作更高效，请遵循下面的流程和规范。

1) 分支与工作流
- 使用 `main` 作为稳定分支。不要直接在 `main` 上开发。
- 新功能/修复请基于 `main` 创建 feature 分支，命名规则：`feature/<描述>` 或 `fix/<描述>`，例如 `feature/add-checkout-transaction`。
- 每项变更通过 Pull Request (PR) 合并到 `main`。

2) 提交规范（简洁且有意义）
- 每个提交信息第一行为简短说明（不超过 72 字符）。
- 详细内容写在空行后，说明变更原因和要点。

3) Pull Request 要求
- PR 标题请简洁说明改动目的。
- 在 PR 描述中包含：问题/目标、变更要点、如何手动测试、关联 Issue（如果有）。
- 指定至少一名同组成员进行 code review 后再合并。

4) 代码风格与测试
- 遵循 PEP8 基本格式。推荐安装并使用 `black` 和 `flake8`。
- 对关键逻辑（调度、账单等）请尽量添加单元测试。

5) 本地开发快速指南
- 创建虚拟环境并安装依赖：
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- 运行迁移并启动开发服务器：
  ```powershell
  python manage.py migrate
  python manage.py runserver
  ```

6) 报告问题
- 请先在 Issues 中搜索是否已有相同问题；若无，创建新 Issue 并按模板填写。对于紧急 bug，请在 Issue 中标注 `priority: high`。

7) 其他
- 请勿将敏感信息（如生产 `SECRET_KEY`、密码、token）提交到仓库。

谢谢！有任何团队协作流程改进建议请在 Issues 中提出。
