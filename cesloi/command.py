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
    output_args: List[str]

    def __init__(self, name, args, separate=" "):
        self.name = name
        self.args = args
        self.separate = separate
        self.name = self.name.replace("@A@", r"(.+)").replace("@C@", r"(\d+)").replace("@B@", r"(\w+)")
        if isinstance(self.args, str):
            self.args = self.args.replace("@A@", "(.+)").replace("@C@", r"(\d+)").replace("@B@", r"(\w+)")

    def analysis_content(self):
        if isinstance(self.args, str):
            return self.name + self.separate + self.args
        elif isinstance(self.args, Subcommand):
            result = self.args.analysis_content()
            if isinstance(result, str):
                return [self.name, self.name + self.separate + result]
            elif isinstance(result, list):
                return [self.name] + [self.name + self.separate + sub for sub in result]
        elif isinstance(self.args, list):
            result = []
            for sub in self.args:
                _result = sub.analysis_content()
                if isinstance(_result, str):
                    result.append(_result)
                elif isinstance(_result, list):
                    result.extend(_result)
            return [self.name] + [self.name + self.separate + sub for sub in result]


class Command:
    headers: List[str]
    main: Optional[Subcommand]

    def __init__(self, headers: List[str], command_list: Optional[list] = None):
        self.headers = headers
        if command_list:
            self.main = self.analysis_subcommand(command_list)
        else:
            self.main = None

    def analysis_subcommand(self, cl):
        if len(cl) < 2:
            raise ValueError
        name, args = cl[0], cl[1]
        if isinstance(args, list):
            if isinstance(args[0], str):
                args = self.analysis_subcommand(args)
            else:
                args = []
                for sub in cl[1]:
                    args.append(self.analysis_subcommand(sub))
        if len(cl) > 2:
            sep = cl[2]
            return Subcommand(name, args, separate=sep)
        return Subcommand(name, args)


class CommandHandle:

    @classmethod
    def analysis_command(cls, command: Command, cmd: str) -> Union[str, Tuple[str], bool]:
        cmd = cmd.rstrip(' ')
        for head in command.headers:
            if head != "" and head in cmd:
                cmd = cmd.replace(head, "", 1)
                break
        if not command.main:
            if cmd == "":
                return True
            return False
        for pat in command.main.analysis_content():
            pattern = re.compile(pat + '$')
            result = pattern.findall(cmd)
            if result:
                return result[0]
        return False


AnyStr = Argument.AnyStr.value
Album = Argument.Album.value
Digit = Argument.Digit.value

if __name__ == "__main__":
    v = Command(headers=[""], command_list=["img", [["download", ["-p", f"{AnyStr}"]],
                                                          ["upload", [["-u", f"{AnyStr}"], ["-f", f"{AnyStr}"]]]]])
    print(CommandHandle.analysis_command(v, "img upload -u http://www.baidu.com"))
    print(CommandHandle.analysis_command(v, "img upload -f img.png"))

    v = Command(headers=["bots","bot"])
    print(CommandHandle.analysis_command(v, "bot"))
    print(CommandHandle.analysis_command(v, "botsbot"))
