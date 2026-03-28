# 黑客松项目：Agent 交互平台后端开发计划

## 一、 项目背景与技术栈评估

当前项目为**黑客松 Demo**，核心业务是一个 **Agent 交互与信用系统平台**。黑客松的特点是**时间紧迫、需求聚焦、演示效果优先**。

基于刚录入的 `backend-standards` 规范，结合黑客松场景，对额外中间件的评估如下：

1.  **RabbitMQ (按需内部使用，不对外暴露)**
    *   **规范契合度**：规范 1.3 节明确指出“中间件服务 (Tools & Plugins) 使用 RabbitMQ 与主服务通信”。
    *   **业务架构调整**：AI Agent **完全通过 REST API** 与主服务交互（如轮询任务、提交结果）。如果你的主服务需要将某些耗时较长的“撮合逻辑”或“数据清洗”放到后台异步执行，可以使用 RabbitMQ。但对于外部的 AI Agent 来说，它们不知道也不需要连接 RabbitMQ。
    *   **结论**：**降级为可选/内部组件**。黑客松初期为了最快跑通，甚至可以先不用，直接在 REST API 中同步处理撮合。

2.  **Redis (建议简化使用或暂缓)**
    *   **业务需求**：通常用于缓存、Session 存储或分布式锁。
    *   **黑客松考量**：对于一个初始 Demo，数据库（如 SQLite/PostgreSQL）的并发压力并不大。为了加快开发速度，减少部署依赖。
    *   **结论**：**按需引入**。初期可仅用于用户 Token 的会话管理或暂不使用（改用 JWT 无状态 Token）。若为了展示“高并发接单”的防超卖逻辑，可引入 Redis 分布式锁作为亮点。

3.  **MinIO (暂缓使用)**
    *   **业务需求**：对象存储，用于存放大文件（图片、文档等）。
    *   **黑客松考量**：如果你的 Task 不涉及大文件上传下载，或者只需要传少量文本数据/JSON 结构，完全可以直接走数据库或本地文件系统。
    *   **结论**：**不使用**。除非 Demo 的核心亮点包含“大文件处理”或“多模态数据交互”，否则徒增部署成本。

**最终核心技术栈选型：**
*   **Web框架**: FastAPI (提供全套 REST API 和 Swagger 给 Agent 调用)
*   **数据库**: SQLite (快速开发) + SQLAlchemy (ORM) + Alembic (迁移)
*   **包管理**: Poetry
*   *(可选内部组件)*: RabbitMQ (仅用于后端内部的异步耗时任务，不对外暴露)

---

## 二、 后端系统架构设计

基于你的需求，系统架构调整为 **RESTful API 驱动模型**：

1.  **主服务 (Main API Service)**: 核心大脑，负责 HTTP 请求、数据库交互、任务撮合逻辑。
2.  **外部 AI Agent**: 独立运行的脚本或程序（可能是 Python、Node.js 等），通过发起 HTTP 请求与主服务交互。

### 核心交互流程 (REST API)
*   **发布**: 雇主 Agent 调用 `POST /api/tasks` 发布任务。
*   **发现/接单**: 劳工 Agent 轮询调用 `GET /api/tasks/open` 寻找任务，然后调用 `POST /api/tasks/{id}/accept` 抢单。
*   **提交**: 劳工 Agent 完成后，调用 `POST /api/tasks/{id}/submit` 提交结果。
*   **评价/结算**: 雇主 Agent 查看结果后，调用 `POST /api/tasks/{id}/rate` 打分并触发积分结算。

### 模块划分 (`src/` 目录下)
*   `auth/`: 认证模块（用户注册、登录、Token 签发）
*   `agent/`: Agent 资料与信用模块（查询积分、信用评价记录）
*   `task/`: 任务大厅模块（发布任务、查询任务状态、任务结算）
*   `mq/` (或 `plugins/`): 消息队列处理模块（RabbitMQ 生产者与消费者封装）

---

## 三、 数据库模型设计 (基于之前的 SQLite 设计转化为 SQLAlchemy)

根据规范 8 (Models)，使用 SQLAlchemy 定义：

1.  **AgentModel** (`agents` 表)
    *   `id`, `username`, `password_hash`, `points`, `is_del` (软删除)
2.  **TaskModel** (`tasks` 表)
    *   `id`, `employer_id`, `title`, `description`, `reward_points`, `status`
3.  **ReputationRecordModel** (`reputation_records` 表)
    *   `id`, `task_id`, `employer_id`, `worker_id`, `points_transferred`, `rating`, `comment`

---

## 四、 开发实施步骤与时间线 (黑客松冲刺版)

### Phase 1: 基础设施搭建 (预计 1-2 小时)
1.  使用 Poetry 初始化项目结构，严格按照规范目录树创建文件夹（`src`, `tests`, `alembic` 等）。
2.  配置 `src/config.py`，使用 Pydantic `BaseSettings` 读取 `.env` 中的数据库路径和 RabbitMQ 连接串。
3.  配置全局日志 `src/logger.py` 和全局异常捕获 `src/exceptions.py`。
4.  初始化 SQLAlchemy 数据库连接 `src/database.py` 和 Alembic 迁移环境。

### Phase 2: 核心 CRUD 业务开发 (预计 3-4 小时)
严格遵循“路由与业务分离”原则 (`router.py` -> `service.py`)。

1.  **认证模块 (`src/auth/`)**
    *   完成注册、登录接口。
    *   定义 `UserSchema`，配置 `from_attributes = True`。
2.  **信用管理模块 (`src/agent/`)**
    *   查询个人积分和历史交易记录。
    *   计算并返回平均信用分。
3.  **任务发布模块 (`src/task/`)**
    *   雇主发布任务，预扣除或冻结积分。
    *   展示任务大厅列表。

### Phase 3: REST API 撮合逻辑闭环 (预计 3-4 小时)
1.  **接单逻辑 (`POST /tasks/{id}/accept`)**: 劳工 Agent 调用接口接单，系统检查任务状态，防超卖，并更新为 `IN_PROGRESS`。
2.  **提交结果 (`POST /tasks/{id}/submit`)**: 劳工 Agent 提交任务结果（可以是结果链接或 JSON 数据）。
3.  **评价与结算 (`POST /tasks/{id}/rate`)**: 雇主确认结果，调用评价接口，系统在同一个事务中执行：扣除雇主积分 -> 增加劳工积分 -> 生成 `ReputationRecord` -> 更新任务为 `COMPLETED`。
4.  *(可选进阶)*: 如果撮合过程需要复杂的 AI 匹配计算（比如判断劳工 Agent 的信誉是否满足雇主的要求），这部分计算逻辑写在主服务的 Service 层中。

### Phase 4: 联调与 Swagger 完善 (预计 1-2 小时)
1.  为所有 Router 添加规范的 Swagger 注解 (`name`, `response_model`, `responses`)。
2.  确保所有接口返回统一的 `BaseResponse` 格式。
3.  编写核心流程的集成测试或提供 Postman/HTTP 脚本以便评委演示。

---

## 五、 给开发者的行动建议

如果你同意这个计划，我们可以按照以下顺序开始写代码：
1.  **第一步**：我帮你生成标准的项目目录结构和 `pyproject.toml` (Poetry 依赖)。
2.  **第二步**：我帮你编写核心的 `models.py` (SQLAlchemy 格式) 和 `database.py`。
3.  **第三步**：我们逐个模块 (`auth`, `task`, `agent`) 实现 Router 和 Service，构建完整的 REST API 撮合闭环。