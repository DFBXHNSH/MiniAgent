from src import BaseAgent
from pathlib import Path
import shutil

if __name__ == "__main__":
    # ret = Path("E:\\Program Files\\Git\\Git\\bin\\bash.exe").exists()
    # print(ret)
    # ret = shutil.which("bash")
    # print(ret)
    # Create an instance of the BaseAgent class
    agent = BaseAgent(model="dashscope/qwen-turbo")
    ret = agent.run("运行bash中的ls命令然后返回结果", verbose=True)
    print(ret)

    