\# mini\_agent 项目说明文档



\## 概述

`mini\_agent` 是一个轻量、模块化的大语言模型智能体框架，具备工具调用能力，基于 Python 与 `litellm` 库构建。它使用通义千问（DashScope/Qwen）模型进行推理，并遵循\*\*高内聚、低耦合\*\*的设计原则，保证可维护性与扩展性。



\## 快速开始



\### 环境要求

\- Python 3.8+

\- 安装依赖（建议使用虚拟环境）

&nbsp; ```bash

&nbsp; pip install litellm dashscope

&nbsp; ```

\- 配置 DashScope API 密钥（使用 Qwen 模型必需）

&nbsp; ```bash

&nbsp; export DASHSCOPE\_API\_KEY="你的API密钥"

&nbsp; ```



\### 基础使用

```python

from src import BaseAgent



\# 初始化智能体

agent = BaseAgent(model="dashscope/qwen-turbo")



\# 执行简单任务（如列出当前目录文件）

response = agent.run("列出当前目录下的所有文件")

print(response)



\# 交互式对话模式

agent.chat(verbose=True)

```



\### 进阶使用（子智能体 + 技能）

```python

from src import BaseAgent



\# 启用子智能体，支持探索/编码/规划三类任务

agent = BaseAgent(model="dashscope/qwen-turbo", enable\_subagent=True)



\# 自动调用内置代码审查技能

response = agent.run(

&nbsp;   "检查这个函数的bug和代码规范：\\n\\n"

&nbsp;   "def calculate\_average(numbers):\\n"

&nbsp;   "    total = 0\\n"

&nbsp;   "    for n in numbers:\\n"

&nbsp;   "        total += n\\n"

&nbsp;   "    return total / len(numbers)"

)



\# 查看技能使用次数

print(f"已使用技能数：{agent.get\_skill\_count()}")

```



\## 项目结构

代码按模块化组织，职责清晰分离：

```

src/

├── agent/          # 智能体实现（核心/子智能体）

├── tools/          # 工具定义、执行与安全校验

├── llm/            # LLM 客户端封装（litellm 集成）

├── compression/    # 对话历史压缩策略

├── logging/        # 内部日志与格式化打印

├── messages/       # 消息构建工具

├── prompts/        # 系统提示词与提醒

├── skills/         # 领域知识（技能）加载系统

└── \_\_init\_\_.py     # 对外 API 导出

```



\## 核心功能



\### 1. 工具调用系统

框架内置一套实用工具集，支持真实任务执行：



| 工具 | 说明 |

|------|------|

| `bash` | 执行 shell 命令 |

| `read\_file` | 安全读取文件内容 |

| `write\_file` | 创建/覆盖文件 |

| `edit\_file` | 精准文本替换编辑 |

| `todo` | 多步骤任务跟踪（最多20条） |

| `run\_task` | 启动专业子智能体 |

| `skill` | 按需加载领域知识 |



\### 2. 子智能体系统

开启 `enable\_subagent=True` 后，主智能体可创建三类专业子智能体：

\- `explore`：信息探索与资料搜集

\- `code`：代码编写与调试

\- `plan`：任务规划与拆解

\- 子智能体运行在独立上下文（不继承父对话历史）

\- 不支持递归创建子智能体（避免无限循环）



\### 3. 历史压缩

支持两种可插拔的上下文压缩策略，优化 Token 消耗：

\- \*\*滑动窗口\*\*：只保留最近 N 轮对话

\- \*\*语义摘要\*\*：用 LLM 对早期对话做摘要

\- 通过 `compression\_type` 配置：`"sliding"`、`"semantic"`、`"auto"` 或 `"none"`



\### 4. 技能系统（领域知识）

技能是基于 Markdown 的可编辑知识包，智能体可按需加载：

\- \*\*渐进式加载\*\*：元数据 → 完整内容 → 资源文件，保持上下文精简

\- \*\*内置技能\*\*：`code-review`（代码审查）、`git`（Git 操作）

\- \*\*自定义技能\*\*：在 `skills/` 下新建文件夹，编写 `SKILL.md` 即可扩展



\### 5. 安全与防护

\- 路径安全校验（`tools/safety.py`），禁止访问工作区外文件

\- 待办事项约束：最多 20 条，同一时间仅 1 条进行中

\- 超时提醒：超过10轮未更新待办时自动提醒



\## 架构设计



\### 智能体执行流程

1\. \*\*入口\*\*：`BaseAgent.run()` 接收用户输入并初始化

2\. \*\*压缩\*\*：按配置对历史消息进行压缩

3\. \*\*工具循环\*\*：循环执行直到 LLM 返回纯文本结果：

&nbsp;  - 调用 LLM，传入当前消息 + 可用工具

&nbsp;  - 执行模型选择的工具

&nbsp;  - 将工具结果追加到对话历史

4\. \*\*返回\*\*：输出最终回复并更新历史



\### 核心设计原则

\- \*\*高内聚\*\*：每个模块只负责一件明确的事

\- \*\*低耦合\*\*：模块通过清晰接口交互，依赖最小化

\- \*\*可插拔\*\*：压缩策略、工具、技能均可独立扩展

\- \*\*缓存友好\*\*：技能内容以用户消息注入，不修改系统提示，保护模型缓存



\## 重要说明

1\. \*\*路径安全\*\*：所有文件操作限制在工作区内，防止越权访问

2\. \*\*日志\*\*：`logging/formatter.py` 为内部调试使用，不属于对外 API

3\. \*\*模型兼容\*\*：默认适配通义千问，可通过 `model` 参数切换其他 litellm 支持的模型

4\. \*\*技能缓存\*\*：技能内容以工具结果形式传入，优化 Token 与缓存效率



\## 框架扩展



\### 添加自定义工具

1\. 在 `tools/definitions.py` 定义工具 schema

2\. 在 `tools/implementations.py` 实现逻辑

3\. 在 `tools/executor.py` 注册工具



\### 创建自定义技能

1\. 在 `skills/` 新建文件夹（如 `skills/my-skill/`）

2\. 编写 `SKILL.md`，包含 YAML 头信息（名称/描述）+ Markdown 内容

3\. （可选）添加 `scripts/`、`references/`、`assets/` 存放辅助资源



\### 新增压缩策略

1\. 在 `compression/` 新建文件（如 `compression/custom.py`）

2\. 实现 `CompressionStrategy` 抽象基类

3\. 在智能体配置中注册新策略



---



\## 总结

\- `mini\_agent` 是模块化 LLM 智能体框架，支持工具调用，基于 Python/litellm，专为通义千问优化

\- 核心能力：子智能体、历史压缩、安全工具执行、灵活技能系统

\- 设计亮点：高内聚低耦合、组件可插拔、提示词缓存高效

\- 易于扩展：自定义工具、技能、压缩策略，同时保持安全与性能

