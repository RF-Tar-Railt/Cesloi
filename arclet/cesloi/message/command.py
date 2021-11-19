from typing import List, Union, Tuple, Optional
from enum import Enum
import re


class Argument(Enum):
    AnyStr = "@A@"
    Album = "@B@"
    Digit = "@C@"


class Subcommand:
    name: Union[str, List[str]]
    separate: str
    args: Union[str, "Subcommand", List["Subcommand"]]

    def __init__(self, name, args: Optional[Union[str, "Subcommand", List["Subcommand"]]] = None, separate=" "):
        self.name = name
        self.args = args or ""
        self.separate = "" if self.args == "" else separate
        self.name = self.name.replace("@A@", r"(.+)").replace("@C@", r"(\d+)").replace("@B@", r"(\w+)")
        if isinstance(self.args, str):
            self.args = self.args.replace("@A@", "(.+)").replace("@C@", r"(\d+)").replace("@B@", r"(\w+)")

    def analysis_content(self):
        if isinstance(self.args, str):
            return [self.name + self.separate + self.args]
        elif isinstance(self.args, Subcommand):
            if self.name.rstrip(' ') == "":
                return [self.name + self.separate + sub for sub in self.args.analysis_content()]
            return [self.name + self.separate + sub for sub in self.args.analysis_content()] + [self.name]
        elif isinstance(self.args, list):
            result = []
            for sub in self.args:
                result.extend(sub.analysis_content())
            if self.name.rstrip(' ') == "":
                return [self.name + self.separate + sub for sub in result]
            return [self.name + self.separate + sub for sub in result] + [self.name]


class Command:
    """命令/命令参数解析器

    样例：Command(headers=[""], main=["name","args/subcommand/subcommand_list","separate"])

    其中
        - name: 命令名称, 必写
        - args: 命令参数, 可选
        - separate: 命令分隔符,分隔name与args,通常情况下为 " " (空格), 可选
        - subcommand: 子命令, 格式与main相同
        - subcommand_list: 子命令集, 可传入多个子命令
    name与args接受Command提供的三个参数: AnyStr, Album, Digit, 即name/args接受 任意字符/字母数字组合/纯数字

    您也可以用自己的写的正则表达式,前提是需要用括号括起来,如(.*?)

    Args:
        headers: 呼叫该命令的命令头，一般是你的机器人的名字，可选
        main: 命令主体，你的命令的主要参数解析部分，可选
    """
    headers: Optional[List[str]]
    main: Optional[Subcommand]

    def __init__(self, headers: Optional[List[str]] = None, main: Optional[list] = None):
        if not headers and not main:
            raise ValueError("Must choose one parameter!")
        self.headers = headers or [""]
        if main:
            self.main = self.to_subcommand(main)
        else:
            self.main = None

    def to_subcommand(self, cl):
        if not cl:
            raise ValueError("Must input name!")
        name = cl[0]
        if len(cl) > 1:
            args = cl[1]
            if isinstance(args, list):
                if isinstance(args[0], str):
                    args = self.to_subcommand(args)
                else:
                    args = []
                    for sub in cl[1]:
                        args.append(self.to_subcommand(sub))
            if len(cl) > 2:
                sep = cl[2]
                return Subcommand(name, args, separate=sep)
            return Subcommand(name, args)
        return Subcommand(name)

    def analysis(self, cmd: str) -> Union[str, Tuple[str], bool]:
        cmd = cmd.rstrip(' ')
        for head in self.headers:
            if head != "" and head in cmd:
                cmd = cmd.replace(head, "", 1)
                break
        cmd = cmd.lstrip(' ')
        if not self.main:
            if cmd == "":
                return True
            return False
        for pat in self.main.analysis_content():
            pattern = re.compile('^' + pat + '$')
            result = pattern.findall(cmd)
            if result:
                if result[0] == cmd:
                    return True
                return result[0]
        return False


AnyStr = Argument.AnyStr.value
Album = Argument.Album.value
Digit = Argument.Digit.value

if __name__ == "__main__":
    """
    演示程序
    """
    v = Command(main=["img", [["download", ["-p", AnyStr]],
                              ["upload", [["-u", AnyStr], ["-f", AnyStr]]]]])
    print(v.analysis("img upload -u http://www.baidu.com"))  # http://www.baidu.com
    print(v.analysis("img upload -f img.png"))  # img.png

    v = Command(headers=['bot', 'cmd.'], main=["", [["签到"], ["sign in"]], ""])
    print(v.analysis("cmd.sign in"))  # True

    v = Command(headers=["bots", "bot"])
    print(v.analysis("bot"))  # True
    print(v.analysis("bots aaa"))  # False

    v = Command(headers=["bots", "bot"], main=[AnyStr])
    print(v.analysis("bot"))  # False
    print(v.analysis("bots aaa"))  # True

    v = Command(main=[".command", ["--option", "foo"]])
    print(v.analysis(".command --option foo"))  # True
    print(v.analysis(".command "))

    v = Command(main=[f"/ping {AnyStr}", [["-t", Digit], ["-a"]]])
    print(v.analysis("/ping 127.0.0.1 -t 10"))
    print(v.analysis("/ping 127.0.0.1"))
    print(v.analysis("/ping 127.0.0.1 -a"))
