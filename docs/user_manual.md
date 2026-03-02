# mini_agent 用户手册

## 简介

mini_agent 是一个轻量级的 LLM 代理框架，支持工具调用、子代理、技能系统等功能。本手册面向开发者，帮助你快速上手和使用。

## 快速开始

### 安装依赖

```bash
pip install litellm python-dotenv
```

### 基础用法

```python
from src import BaseAgent

# 创建代理
agent = BaseAgent(model="dashscope/qwen-turbo")

# 执行任务
response = agent.run("列出当前目录的文件")
print(response)
```

### 交互式聊天

```python
from src import BaseAgent

agent = BaseAgent(model="dashscope/qwen-turbo")
agent.chat(verbose=True)
```

## 核心功能

### 1. 内置工具

代理内置以下工具，可直接调用：

| 工具 | 功能 | 示例 |
|------|------|------|
| `bash` | 执行 shell 命令 | `ls -la`, `git status` |
| `read_file` | 读取文件内容 | 读取 `.py`, `.md` 文件 |
| `write_file` | 创建或覆盖文件 | 写入配置文件 |
| `edit_file` | 编辑文件（替换文本） | 修改函数签名 |
| `todo` | 跟踪多步骤任务 | 创建任务清单 |

**使用示例：**

```python
agent = BaseAgent()

# 代理会自动调用 bash 工具
response = agent.run("查看当前目录结构")

# 代理会自动调用 read_file 工具
response = agent.run("读取 README.md 的内容")

# 代理会自动调用 write_file 工具
response = agent.run("创建一个名为 hello.py 的文件，内容是 print('Hello World')")

# 代理会自动使用 todo 工具
response = agent.run("完成一个任务：1. 创建文件 2. 写入内容 3. 运行测试")
```

### 2. 子代理系统

对于复杂任务，可以启用子代理：

```python
agent = BaseAgent(enable_subagent=True)

# 代理会自动判断何时创建子代理
response = agent.run("分析整个代码库，找出所有使用数据库的地方")

# 子代理类型：
# - explore: 快速浏览代码库
# - code: 处理代码相关任务
# - plan: 制定执行计划
```

### 3. 技能系统

代理内置了领域知识技能，任务匹配时会自动加载：

```python
agent = BaseAgent()

# Git 操作 - 自动加载 git 技能
response = agent.run("创建一个新分支并切换到该分支")

# 代码审查 - 自动加载 code-review 技能
response = agent.run("审查这段代码是否有安全问题：\npassword = input()")
```

**可用技能：**

| 技能 | 描述 |
|------|------|
| `git` | Git 版本控制操作 |
| `code-review` | 代码审查、Bug 和安全检查 |

### 4. 历史压缩

长对话时会自动压缩历史记录，节省 token：

```python
# 滑动窗口压缩（保留最近 N 轮）
agent = BaseAgent(
    enable_compression=True,
    compression_type="sliding",
    compression_interval=20  # 每 20 轮压缩一次
)

# 语义摘要压缩（用 LLM 总结早期对话）
agent = BaseAgent(
    enable_compression=True,
    compression_type="semantic"
)

# 自动模式（根据对话长度智能选择）
agent = BaseAgent(
    enable_compression=True,
    compression_type="auto"
)
```

### 5. 自定义工具

你可以注册自己的工具：

```python
from src import BaseAgent

agent = BaseAgent()

@agent.register_tool()
def calculate(expression: str) -> str:
    """安全计算数学表达式。"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

# 代理现在可以使用 calculate 工具
response = agent.run("计算 2 * (3 + 4) 的结果")
```

### 6. 自定义系统提示词

```python
agent = BaseAgent(
    system_prompt="你是一个 Python 专家，总是使用类型提示。"
)

response = agent.run("写一个函数，计算两个数的平均值")
```

### 7. 工作目录配置

通过环境变量设置工作目录：

```bash
# Linux/macOS
export MINI_AGENT_WORKDIR=/path/to/project

# Windows PowerShell
$env:MINI_AGENT_WORKDIR="C:\path\to\project"

# Windows CMD
set MINI_AGENT_WORKDIR=C:\path\to\project
```

或者在 Python 中设置：

```python
import os
os.environ["MINI_AGENT_WORKDIR"] = "/path/to/project"
```

## 完整示例

### 示例 1：代码生成与执行

```python
from src import BaseAgent

agent = BaseAgent()

# 创建一个 Python 脚本并运行
response = agent.run("""
创建一个名为 stats.py 的文件，实现以下功能：
1. 定义一个函数 calculate_stats(numbers) 计算平均值、最大值、最小值
2. 包含测试代码
3. 运行文件并查看输出
""")
```

### 示例 2：Git 操作

```python
from src import BaseAgent

agent = BaseAgent()

# 执行完整的 Git 工作流
response = agent.run("""
执行以下 Git 操作：
1. 查看当前状态
2. 创建一个新分支 feature/new-feature
3. 切换到该分支
4. 创建一个文件 test.txt 并提交
5. 查看提交历史
""")
```

### 示例 3：代码审查

```python
from src import BaseAgent

agent = BaseAgent()

code = '''
def get_user_input():
    password = input("Enter password: ")
    save_to_database(password)
    return password
'''

response = agent.run(f"审查这段代码，找出潜在的安全问题：\n{code}")
print(response)
```

### 示例 4：多步骤项目任务

```python
from src import BaseAgent
import os

# 设置工作目录
os.environ["MINI_AGENT_WORKDIR"] = "./my_project"

agent = BaseAgent(enable_subagent=True)

response = agent.run("""
创建一个简单的 Web API 项目：
1. 创建项目目录结构
2. 编写主程序文件
3. 添加路由处理函数
4. 创建 requirements.txt
5. 编写 README.md
""")
```

### 示例 5：交互式聊天模式

```python
from src import BaseAgent

# 启用详细输出，查看执行过程
agent = BaseAgent(verbose=True, enable_subagent=True)

# 进入交互模式
agent.chat()
```

在交互模式下，你可以：
- 输入任意任务
- 代理会自动选择合适的工具
- 按 `Ctrl+C` 退出

## 配置参数

### BaseAgent 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | str | `"dashscope/qwen-turbo"` | 使用的 LLM 模型 |
| `enable_subagent` | bool | `False` | 是否启用子代理 |
| `enable_compression` | bool | `False` | 是否启用历史压缩 |
| `compression_type` | str | `"auto"` | 压缩类型：`"sliding"`, `"semantic"`, `"auto"`, `"none"` |
| `compression_interval` | int | `20` | 压缩间隔（轮次） |
| `system_prompt` | str | `None` | 自定义系统提示词 |
| `verbose` | bool | `False` | 是否显示详细日志 |

### 方法列表

| 方法 | 说明 |
|------|------|
| `run(user_input)` | 执行单次任务 |
| `chat(verbose=False)` | 启动交互式聊天 |
| `reset()` | 重置对话历史 |
| `get_history()` | 获取对话历史 |
| `get_skill_count()` | 获取使用的技能数量 |
| `register_tool()` | 装饰器，注册自定义工具 |

## 常见问题

### Q: 如何切换 LLM 模型？

```python
# 使用不同的模型
agent = BaseAgent(model="gpt-4")
agent = BaseAgent(model="claude-3-opus-20240229")
```

### Q: 如何查看代理执行的详细过程？

```python
# 启用 verbose 模式
agent = BaseAgent(verbose=True)
response = agent.run("你的任务")
```

### Q: 如何重置对话历史？

```python
agent = BaseAgent()

# 执行一些任务
agent.run("任务 1")
agent.run("任务 2")

# 重置历史
agent.reset()

# 现在对话从新开始
agent.run("任务 3")
```

### Q: 如何限制代理的文件访问范围？

代理通过工作目录限制访问范围。设置工作目录后，代理只能访问该目录下的文件：

```python
import os
os.environ["MINI_AGENT_WORKDIR"] = "/safe/directory"

agent = BaseAgent()
```

### Q: Todo 任务有限制吗？

有的，限制如下：
- 最多 20 个任务
- 同时只能有 1 个任务处于 `in_progress` 状态
- 每个任务必须包含：`content`、`status`、`activeForm`

### Q: 如何创建自己的技能？

1. 在项目根目录的 `skills/` 文件夹中创建新目录
2. 创建 `SKILL.md` 文件，格式如下：

```markdown
---
name: my-skill
description: 执行特定的复杂任务
---

# My Skill

使用此技能当用户请求 [描述何时使用]。

## 步骤

1. 首先，做这个...
2. 然后，做那个...

## 示例

### 示例 1
```bash
命令示例
```

### 示例 2
```python
代码示例
```
```

3. 代理会自动识别并使用该技能

### Q: 如何调试工具调用？

启用 verbose 模式可以看到详细的工具调用日志：

```python
agent = BaseAgent(verbose=True)
```

输出示例：
```
[14:23:45.123] [Agent] 🔧 Tool Calls:
[14:23:45.124] [Agent]    1. bash({"command": "ls -la"})

[14:23:45.200] [Agent] 📊 Tool Results:
[14:23:45.201] [Agent]    1. bash: drwxr-xr-x  4 user group ...
```

## 最佳实践

### 1. 使用合适的模型

- **快速/简单任务**: `dashscope/qwen-turbo`
- **复杂推理任务**: `gpt-4` 或 `claude-3-opus-20240229`

### 2. 启用子代理处理复杂任务

对于需要深度分析代码库的任务，启用子代理：

```python
agent = BaseAgent(enable_subagent=True)
```

### 3. 使用 Todo 跟踪多步骤任务

明确告诉代理使用 todo 工具：

```python
response = agent.run("""
使用 TodoWrite 工具跟踪以下任务：
1. 读取配置文件
2. 修改配置
3. 保存文件
4. 重启服务
""")
```

### 4. 分阶段执行复杂任务

对于非常复杂的任务，分阶段执行：

```python
agent = BaseAgent()

# 阶段 1：分析
agent.run("分析这个项目的结构")

# 阶段 2：规划
agent.run("制定一个重构计划")

# 阶段 3：执行
agent.run("按照计划执行重构")
```

### 5. 合理使用历史压缩

对于长时间运行的会话，启用压缩：

```python
agent = BaseAgent(
    enable_compression=True,
    compression_type="auto"
)
```

## 高级用法

### 获取对话历史

```python
history = agent.get_history()
print(f"对话包含 {len(history)} 条消息")
```

### 统计技能使用

```python
agent = BaseAgent()
agent.run("执行一些任务...")

print(f"使用了 {agent.get_skill_count()} 个技能")
```

### 组合使用多个功能

```python
agent = BaseAgent(
    model="dashscope/qwen-turbo",
    enable_subagent=True,
    enable_compression=True,
    compression_type="auto",
    verbose=True
)

# 定义自定义工具
@agent.register_tool()
def search_code(pattern: str) -> str:
    """在代码库中搜索模式。"""
    import subprocess
    result = subprocess.run(
        ["grep", "-r", pattern, "src/"],
        capture_output=True,
        text=True
    )
    return result.stdout

# 执行任务
agent.run("""
任务：
1. 使用 search_code 搜索所有使用数据库的代码
2. 分析找到的代码
3. 使用 todo 工具跟踪分析步骤
4. 生成分析报告
""")
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `MINI_AGENT_WORKDIR` | 代理的工作目录路径 |

## 相关资源

- [工程文档](index.md) - 详细的模块文档和实现细节
- [项目 README](../README.md) - 项目概述
- [CLAUDE.md](../CLAUDE.md) - Claude Code 使用指南

## 版本

当前版本：基于 `mini_agent` 项目开发

## 支持

如有问题或建议，请参考项目文档或提交 Issue。
