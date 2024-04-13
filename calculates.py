"""
Filename: MetaGPT/examples/build_customized_multi_agents.py
Created Date: Wednesday, November 15th 2023, 7:12:39 pm
Author: garylin2099
"""
import re

import fire

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


def parse_code(rsp):
    pattern = r"```python(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1) if match else rsp
    return code_text


class SimpleWriteCode(Action):
    PROMPT_TEMPLATE: str = """
    用python编写程序，实现{instruction}.
    返回 ```python your_code_here ``` ，不要其他文字,
    你的代码:
    """
    name: str = "编写代码"

    async def run(self, instruction: str):
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)

        rsp = await self._aask(prompt)

        code_text = parse_code(rsp)

        return code_text


class SimpleCoder(Role):
    name: str = "张程序员"
    profile: str = "程序员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement])
        self.set_actions([SimpleWriteCode])


class SimpleWriteTest(Action):
    PROMPT_TEMPLATE: str = """
    Context: {context}
    编写 {k} 个 测试用例，假设您已经导入了pytest，使用pytest对给定的函数进行测试.
    返回 ```python your_code_here ``` ，不要其他文本返回,
    你的代码:
    """

    name: str = "编写测试用例"

    async def run(self, context: str, k: int = 3):
        prompt = self.PROMPT_TEMPLATE.format(context=context, k=k)

        rsp = await self._aask(prompt)

        code_text = parse_code(rsp)

        return code_text


class SimpleTester(Role):
    name: str = "李测试"
    profile: str = "测试工程师"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteTest])
        # self._watch([SimpleWriteCode])
        self._watch([SimpleWriteCode, SimpleWriteReview])  # feel free to try this too

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # context = self.get_memories(k=1)[0].content # use the most recent memory as context
        context = self.get_memories()  # use all memories as context

        code_text = await todo.run(context, k=3)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))

        return msg


class SimpleWriteReview(Action):
    PROMPT_TEMPLATE: str = """
    Context: {context}
    审查测试用例并提供一个关键评论:
    """

    name: str = "编写审查意见"

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)

        return rsp


class SimpleReviewer(Role):
    name: str = "王审查"
    profile: str = "代码审查员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteReview])
        self._watch([SimpleWriteTest])


async def main(
        idea: str = "编写一个函数，计算两个数的乘积。",
        investment: float = 3.0,
        n_round: int = 10,
        add_human: bool = False,
):
    logger.info(idea)

    team = Team()
    team.hire(
        [
            SimpleTester(),
            SimpleReviewer(is_human=add_human),
            SimpleCoder(),
        ]
    )

    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


if __name__ == "__main__":
    fire.Fire(main)
