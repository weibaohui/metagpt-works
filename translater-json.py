import os
import re
import fire
from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team


# 在blazork8s中，我使用json存储了k8s术语对应各语言的翻译。
# 我用汉语的zh-CN.json为基准，分割为6个json文件，每个文件存储100条。100条比较方便大模型进行翻译
# 本程序，对每一个分割json文件进行翻译，并另存为json
# 最后，将所有的翻译json文件，按顺序合并为一个json文件
# 那么我们得到了一个全新的翻译文件。


def parse_code(rsp):
    pattern = r"```text(.*)```"
    match = re.search(pattern, rsp, re.DOTALL)
    code_text = match.group(1) if match else rsp
    return code_text


def clean_text(text: str):
    text = text.replace("```json", "").replace("```", "").replace("{", "").replace("}", "")
    # 去掉包裹符号，增加最后的逗号，一切为了方便粘贴拼装
    if not text.endswith(","):
        text += ","
    return text


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


class ActionTextWriter(Action):
    name: str = "保存文本"

    async def run(self, filepath: str, context: str):
        # 读取文本
        with open(filepath, "w") as file:
            context = clean_text(context)

            file.write(context)
            return context


class RoleTextWriter(Role):
    name: str = "司马迁"
    profile: str = "文本保存员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ActionTextTranslate])
        self.set_actions([ActionTextWriter])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: 执行 {self.rc.todo}({self.rc.todo.name})")
        todo = self.rc.todo

        # 第一个环节就是读取文件，所以第一个记忆就是最开始读取的文件地址
        filepath = self.get_memories(k=0)[0].content + "-fanyi.json"  # use the most recent memory as context
        # 最后一个环节是翻译，翻译完了保存，所以通过最后一个记忆获得要写入的文本内容
        context = self.get_memories()[-1].content
        code_text = await todo.run(filepath=filepath, context=context)  # specify arguments
        msg = Message(content=code_text, role=self.profile, cause_by=type(todo))
        return msg


class RoleTextTranslate(Role):
    name: str = "诸葛亮"
    profile: str = "关键字提取员"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([ActionTextReader])
        self.set_actions([ActionTextTranslate])


class ActionTextTranslate(Action):
    PROMPT_TEMPLATE: str = """
    {context}
    
    上面是一份k8s专业术语的翻译对照表。采用json格式存储。
    key为术语，value为对应的翻译。请你将这份对照表翻译为德语。
    key请保持为英文，绝对不要将key进行变更。
    这份翻译表很长，请不要中断，一次性输出完毕。
    请严格按照原来的json格式的返回 ，不要其他任何多余的文字。
    """

    name: str = "提取关键字"

    async def run(self, context: str):
        prompt = self.PROMPT_TEMPLATE.format(context=context)

        rsp = await self._aask(prompt)

        code_text = parse_code(rsp)

        return code_text


async def main(
        idea: str = "",
        investment: float = 3.0,
        n_round: int = 3,
        add_human: bool = False,
):
    logger.info(idea)

    team = Team()
    team.hire(
        [
            RoleTextReader(),
            RoleTextTranslate(),
            RoleTextWriter(),

        ]
    )

    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


async def process_all():
    folder_path = '/Users/weibh/projects/csharp/blazork8s/BlazorApp/wwwroot/lang/splite'
    razor_files = [os.path.join(root, file) for root, dirs, files in os.walk(folder_path) for file in files if
                   file.endswith('.json')]
    for file in razor_files:
        print(f"{file}")
        await main(idea=file)

    # 读取所有的翻译文件
    translate_files = [os.path.join(root, file) for root, dirs, files in os.walk(folder_path) for file in files if
                       file.endswith('-fanyi.json')]
    translate_files.sort()
    # 合并所有的翻译文件
    result = "{"
    for file in translate_files:
        with open(file, "r") as fr:
            result = result + fr.read()
    result = result + "}"
    # 写入最终一个文件
    with open(folder_path + "/fanyi-all.json", "w") as file:
        file.write(result)


if __name__ == "__main__":
    fire.Fire(process_all)
