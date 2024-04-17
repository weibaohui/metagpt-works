import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.libs.kubectl import kubectl


async def main(requirement: str):
    role = DataInterpreter(tools=["kubectl"])  # integrate the tool
    result = await role.run(requirement)
    print(f"执行结果:\r{result}")



async def main2():
    print(await kubectl("kubectl get pods -A"))


if __name__ == "__main__":
    requirement = "执行kubectl get pods -A。请不要使用await方法调用。"
    asyncio.run(main(requirement))
    # print(kubectl("kubectl get pods -A"))
