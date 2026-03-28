---
name: "backend-standards"
description: "Provides backend coding standards and guidelines for the LumenShade project. Invoke when writing, reviewing, or refactoring backend code."
---

# 后端代码规范

采用 FastAPI 框架，自带 Swagger 等开发组件。

## 1. 项目结构

```text
backend/
├── alembic/              # 数据库迁移脚本
├── src/                  # 源代码目录
│   ├── auth/             # [示例] 认证模块
│   │   ├── router.py     # 路由定义
│   │   ├── schemas.py    # 业务逻辑实体类 (Pydantic)
│   │   ├── models.py     # 数据库模型类 (SQLAlchemy)
│   │   ├── dependencies.py
│   │   ├── config.py     # 模块配置
│   │   ├── constants.py  # 常量
│   │   ├── exceptions.py # 模块异常
│   │   ├── service.py    # 业务逻辑函数
│   │   └── utils.py      # 模块工具类
│   ├── paper_generate/   # [示例] 论文生成模块
│   │   └── ...
│   ├── config.py         # 全局配置
│   ├── plugins/          # 插件主服务入口
│   ├── tools/            # 插件逻辑定义部分
│   ├── utils/            # 全局工具包
│   ├── models.py         # 全局模型
│   ├── exceptions.py     # 全局异常
│   ├── pagination.py     # 全局分页模块
│   ├── database.py       # 数据库连接处理
│   └── main.py           # 程序入口
├── tests/                # 测试目录
├── requirements.txt
├── .env                  # 环境变量
├── .gitignore
└── alembic.ini
```

### 模块划分原则
*   `src` 目录下，每个文件夹对应一个业务模块。
*   每个模块一般需包含：
    *   `router.py`: 定义路由
    *   `schema.py`: 定义业务逻辑实体类
    *   `service.py`: 定义业务函数
*   不要将所有路由放在一个文件夹下，应按模块划分。
*   `service` 和 `utils` 可以是文件，也可以是文件夹。

### 可复用工具 (Utils)
*   **全局 Utils**: `src/utils` 供所有模块调用。
*   **模块 Utils**: 特定模块内部使用的工具函数。
*   **解耦原则**: 能放在公共 utils 的尽量放公共区域，只有与模块强关联的才放在特定模块中。

### 中间件服务 (Tools & Plugins)
*   相当于中间件服务，使用 **RabbitMQ** 与主服务通信。
*   支持分布式部署。
*   `Tools`: 定义插件服务的核心逻辑及包装服务类。
*   `Plugins`: 插件启动入口类，负责启动所有插件。

---

## 2. 配置管理

*   使用 Pydantic 的 `BaseSettings`。
*   配置文件位置：模块目录下的 `config.py` 和 `src/config.py`。
*   读取源：项目目录下的 `.env` 文件。
*   **优先级**：当前终端环境变量 > `.env` 文件 > `config.py` 中的默认值。

---

## 3. 日志管理

*   直接导入 `src.logger`：
    ```python
    from src.logger import logger
    
    logger.info("message")
    logger.warning("message")
    logger.error("message")
    ```
*   日志会输出到标准错误流中。

---

## 4. 异常处理与错误返回

为了方便定位和对接，严格区分 **业务错误** 和 **HTTP 系统错误**。

### 异常分类
1.  **自定义基础异常 (业务错误)**
    *   处理方式：封装在 `ResponseModelNoData` 中返回。
    *   HTTP 状态码：**200**。
    *   错误信息：通过 Response Body 中的 `code` 字段区分。
2.  **自定义 HTTP 异常 (系统错误)**
    *   场景：身份验证失败 (401)、权限不足 (403)、服务器内部错误 (500)。
    *   处理方式：直接在路由中 `raise`。

### 返回规范
*   发生业务异常时，使用 `BaseResponseNoData(exception=e)` 返回。
*   修改错误码时，直接在 Router 中抛出异常，框架会自动捕获。

---

## 5. 路由 (Router) 规范

### 命名规范
*   遵循 **Restful** 风格。
*   使用 **中划线 (-)**，禁止使用下划线。
*   必须包含根路由名前缀：
    ```python
    router = APIRouter(prefix="/paper-generate", tags=["PaperGenerate"])
    ```

### 撰写说明
编写路由时需包含完整的 Swagger 注解：
```python
@router.post(                                     # 1. 方法
    "/generate",                                  # 2. 路径
    name="生成论文",                               # 3. 名称 (Swagger显示)
    response_model=BaseResponse[dict],            # 4. 返回数据体类型
    responses={200: {"description": "成功"}}       # 5. HTTP状态码说明
)
def generate_paper(
    params: GenerateParams,                       # 7. 请求体参数 (自动校验)
    db: Session = Depends(get_db)                 # 8. 依赖注入
):
    """
    这里是详细的路由描述，会展示在 Swagger 界面中。
    """
    pass
```

### 逻辑要求
*   **路由与业务分离**：Router 函数中**不要**包含复杂的业务逻辑。
*   业务逻辑应当放到 `service.py` 中实现。

---

## 6. 服务 (Service) 规范

*   业务逻辑全部放在 `service.py` 中。
*   函数应尽量解耦。
*   必须添加类型说明（参数类型、返回值类型）。
*   编写规范的函数注释（Google 风格）。

---

## 7. 业务逻辑类 (Schemas)

`schemas` 用于定义前后端交互的模型 (Request/Response)。

*   **使用枚举类**：对于有限的可能值，使用枚举（变量名大写，值小写）。
*   **类型注释**：使用 `Field(..., description="描述")` 为所有变量添加描述。
*   **默认值**：需要添加默认值。
*   **ORM 转换**：
    为了支持直接将数据库模型转换为 Pydantic 模型，必须添加 Config：
    ```python
    class UserSchema(BaseModel):
        id: int
        username: str
        
        class Config:
            from_attributes = True  # 自动根据字段进行装配
    ```
    *用法示例*：
    ```python
    user_schema = UserSchema.model_validate(db_user)
    ```

---

## 8. 数据表模型 (Models)

`models` 是 SQLAlchemy 的持久化实体类。

*   **类型映射**：尽量使用 `Mapped` 做类型映射。
*   **默认值**：合理使用默认值。
*   **索引**：为经常检索的列添加索引。
*   **注释**：使用 `comment` 参数添加说明。
*   **禁止枚举**：数据表中**不要**使用枚举类（为了便于扩展），枚举只在 schema 中使用。
*   **关联关系**：使用 `relationship` 建立表关系（需配置 `back_populates` 和 `cascade`）。
*   **软删除**：自动注入 `is_del` 属性，查询时过滤 `is_del=False`。

```python
# 关联关系示例
paper_search_histories: Mapped[List["PaperSearchHistory"]] = relationship(
    "PaperSearchHistory",
    back_populates="user",
    cascade="all, delete-orphan"
)
```

---

## 9. 命名规范

*   **文件/变量/函数**：小写字母 + 下划线 (`snake_case`)。
*   **类名**：驼峰命名法 (`PascalCase`)。
*   **私有成员**：
    *   `_variable` (普通私有)
    *   `__variable` (强私有)

---

## 10. 依赖管理 (Poetry)

*   要求 Python 版本 >= 3.8。
*   **安装依赖**：
    ```bash
    poetry install --no-root
    ```
    *(注意：因为项目直接在根目录，需加 `--no-root`)*
*   **常用命令**：
    *   `poetry add <package>`
    *   `poetry update <package>`
    *   `poetry remove <package>`
*   **虚拟环境**：建议修改配置将虚拟环境放在项目内或指定位置：
    ```bash
    poetry config virtualenvs.path <path>
    ```
