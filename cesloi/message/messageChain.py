from typing import List, Iterable, Type, Union

from pydantic import BaseModel

from cesloi.message.element import MessageElement


class MessageChain(BaseModel):
    __root__: List[MessageElement]

    @staticmethod
    def build_chain(obj: List[Union[dict, MessageElement]]):
        elements = []
        for i in obj:
            if isinstance(i, MessageElement):
                elements.append(i)
            elif isinstance(i, dict) and "type" in i:
                for ele in MessageElement.__subclasses__():
                    if ele.__name__ == i["type"]:
                        elements.append(ele.from_json(i))
        return elements

    @classmethod
    def parse_obj(cls: Type["MessageChain"], obj: List[Union[dict, MessageElement]]) -> "MessageChain":
        """内部接口, 会自动将作为外部态的消息元素转为内部态.

        Args:
            obj (List[T]): 需要反序列化的对象

        Returns:
            MessageChain: 内部承载有尽量有效的内部态消息元素的消息链
        """

        return cls(__root__=cls.build_chain(obj))  # 默认是不可变型

    def __init__(self, __root__: Iterable[MessageElement]):
        super().__init__(__root__=self.build_chain(list(__root__)))

    @classmethod
    def create(cls, *elements: Union[Iterable[MessageElement], MessageElement, str]) -> "MessageChain":
        element_list = []
        for ele in elements:
            if isinstance(ele, MessageElement):
                element_list.append(ele)
            elif isinstance(ele, str):
                from .element import Plain
                element_list.append(Plain(ele))
            else:
                element_list.extend(list(ele))
        return cls(__root__=element_list)

    def to_text(self) -> str:
        """获取以字符串形式表示的消息链, 且趋于通常你见到的样子.

        Returns:
            str: 以字符串形式表示的消息链
        """
        return "".join(i.to_text() for i in self.__root__)

    @staticmethod
    def from_text(text: str) -> "MessageChain":
        from .element import Plain
        return MessageChain([Plain(text)])

    def findall(self, element_type: Union[str, MessageElement]):
        if isinstance(element_type, str):
            for ele in MessageElement.__subclasses__():
                if ele.__name__ == element_type:
                    element_type = ele
                    break
        return [i for i in self.__root__ if type(i) is element_type]

    def find(self, element_type: Union[str, MessageElement], index: int = 0):
        ele = self.findall(element_type)
        return False if not ele else ele[index]

    def append(self, element: MessageElement):
        self.__root__.append(element)

    def extend(self, *elements: Union[MessageElement, List[MessageElement]]):
        element_list = []
        for ele in elements:
            if isinstance(ele, MessageElement):
                element_list.append(ele)
            else:
                element_list.extend(ele)
        self.__root__ += element_list

    def copy_self(self):
        return MessageChain(self.__root__)

    def __add__(self, other) -> "MessageChain":
        if isinstance(other, MessageElement):
            self.__root__.append(other)
            return self
        elif isinstance(other, MessageChain):
            self.__root__.extend(i for i in other.__root__ if i.type != "Source")
            return self
        elif isinstance(other, List):
            self.__root__ += other
            return self

    def __repr__(self) -> str:
        return f"MessageChain({repr(self.__root__)})"

    def __iter__(self) -> Iterable[MessageElement]:
        yield from self.__root__

    def __getitem__(self, index):
        return self.__root__[index]

    def __len__(self):
        return len(self.__root__)

    def startswith(self, string: str) -> bool:
        if not self.__root__:
            return False
        return self.to_text().startswith(string)

    def endswith(self, string: str) -> bool:
        if not self.__root__:
            return False
        return self.to_text().endswith(string)
