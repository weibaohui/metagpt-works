"""
Filename: MetaGPT/examples/build_customized_multi_agents.py
Created Date: Wednesday, November 15th 2023, 7:12:39 pm
Author: garylin2099
"""
import os
import re
import fire
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


def parse_code(rsp):
    pattern = r"```text(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1) if match else rsp
    return code_text


class ActionTextReader(Action):
    name: str = "读取文本"

    async def run(self, filepath: str):
        # 读取文本
        with open(filepath, "r") as file:
            content = file.read()
            return content


class RoleTextReader(Role):
    name: str = "王二"
    profile: str = "文本读取员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement])
        self.set_actions([ActionTextReader])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        context = self.get_memories(k=1)[0].content  # use the most recent memory as context
        # context = self.get_memories()  # use all memories as context

        code_text = await todo.run(filepath=context)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


class ActionKeyValueWriter(Action):
    name: str = "保存kv字符串"

    async def run(self, filepath: str, context: str):
        # 读取文本
        with open(filepath, "a") as file:
            file.write(context)
            return context


class RoleKeyValueWriter(Role):
    name: str = "猫老三"
    profile: str = "KV保存员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ActionTextExtraction])
        self.set_actions([ActionKeyValueWriter])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        #
        filepath = "./zh.json"
        # 上一个环节是提取并翻译，翻译完了保存，所以通过最后一个记忆获得要写入的文本内容
        context = self.get_memories()[-1].content
        code_text = await todo.run(filepath=filepath, context=context)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg


class ActionTextWriter(Action):
    name: str = "保存文本"

    async def run(self, filepath: str, context: str):
        # 读取文本
        with open(filepath, "w") as file:
            file.write(context)
            return context


class RoleTextWriter(Role):
    name: str = "司马迁"
    profile: str = "文本保存员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ActionReplaceText])
        self.set_actions([ActionTextWriter])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # 第一个环节就是读取文件，所以第一个记忆就是最开始读取的文件地址
        filepath = self.get_memories(k=0)[0].content  # use the most recent memory as context
        # 最后一个环节是翻译，翻译完了保存，所以通过最后一个记忆获得要写入的文本内容
        context = self.get_memories()[-1].content
        code_text = await todo.run(filepath=filepath, context=context)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg


class RoleTextExtraction(Role):
    name: str = "诸葛亮"
    profile: str = "关键字提取员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ActionTextReader])
        self.set_actions([ActionTextExtraction])


class ActionTextExtraction(Action):
    PROMPT_TEMPLATE: str = """
    {context}
    
    请把上面的字符串中符合```Titile="<value>"```格式的字符串，将value提取出来.
    并按照```"key":"cn",```这样的格式构成，每一行一个kv对，每一行都按```"key":"cn",```这样的格式。其中key是提取出来的value，cn是value的中文翻译。
    最后把全部内容，按照```text 文本内容 ```的格式返回 ，不要其他文本返回,
    你的结果是:
    """

    name: str = "提取关键字"

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)

        code_text = parse_code(rsp)

        return code_text


class ActionReplaceText(Action):
    PROMPT_TEMPLATE: str = """
    {context}
    
    请将上面的内容中符合```Titile="<value>" ```格式的字符串，替换为```Title=@L["value"]```。请注意替换的格式保持一模一样，不要额外加引号包裹.
    将最终结果按照 ```text 文本内容 ```的格式返回 ，不要其他文本返回,
    你的结果是:
    """

    name: str = "替换文本内容"

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)

        code_text = parse_code(rsp)

        return code_text


class RoleReplaceText(Role):
    name: str = "李四"
    profile: str = "文本替换工程师"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ActionReplaceText])
        self._watch([ActionTextExtraction])  # feel free to try this too

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # 第二步是读取的文本内容，从记忆中提取出来
        context = self.get_memories()[1].content  # use the most recent memory as context
        code_text = await todo.run(context=context)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


async def main(
        idea: str = "/Users/weibh/projects/csharp/blazork8s/BlazorApp/Pages/Role/RoleDetailView.razor",
        investment: float = 3.0,
        n_round: int = 3,
        add_human: bool = False,
):
    logger.info(idea)

    team = Team()
    team.hire(
        [
            RoleTextReader(),
            RoleReplaceText(),
            RoleTextExtraction(),
            RoleTextWriter(),
            RoleKeyValueWriter(),

        ]
    )

    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


async def process_all():
    folder_path = '/Users/weibh/projects/csharp/blazork8s/BlazorApp/Pages/'
    razor_files = [os.path.join(root, file) for root, dirs, files in os.walk(folder_path) for file in files if
                   file.endswith('.razor')]
    for file in razor_files:
        print(f"{file}")
        await main(idea=file)


async def filter_all_translate_key_in_folder():
    folder_path = '/Users/weibh/projects/csharp/blazork8s/BlazorApp'
    razor_files = [os.path.join(root, file) for root, dirs, files in os.walk(folder_path) for file in files if
                   file.endswith('.razor') or file.endswith('.cs')]
    for file in razor_files:
        with open(file, 'r') as f:
            text = f.read()
            import re
            pattern = r'L\["([^"]+)"\]'
            matches = re.findall(pattern, text)
            for match in matches:
                print(match)


async def process_it():
    razor_files = [
        "/Users/weibh/projects/csharp/blazork8s/BlazorApp/Pages/EndpointSlice/EndpointSliceDetailView.razor",
        "/Users/weibh/projects/csharp/blazork8s/BlazorApp/Pages/EndpointSlice/EndpointSliceIndex.razor",
        "/Users/weibh/projects/csharp/blazork8s/BlazorApp/Pages/EndpointSlice/EndpointSlicePortView.razor"
    ]
    for file in razor_files:
        print(f"{file}")
        await main(idea=file)


if __name__ == "__main__":
    fire.Fire(filter_all_translate_key_in_folder)
