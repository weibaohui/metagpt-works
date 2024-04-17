import asyncio
import subprocess

from metagpt.tools.tool_registry import register_tool


# Register tool with the decorator
@register_tool()
def kubectl(command: str):
    """
    执行kubectl命令
    """
    if not command.startswith("kubectl"):
        command = "kubectl " + command
    command = ' '.join(command.split())

    # 使用subprocess模块执行命令，捕获标准输出和标准错误
    result = subprocess.run(command,
                            shell=True,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='utf-8')

    # 返回命令执行结果的标准输出
    return result.stdout


if __name__ == '__main__':
    print(kubectl('kubectl get pods -A'))
