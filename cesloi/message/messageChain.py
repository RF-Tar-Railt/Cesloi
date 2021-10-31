from typing import List, Iterable, Type, Union

from pydantic import BaseModel

from cesloi.message.element import MessageElement, _update_forward_refs


class MessageChain(BaseModel):
    __root__: List[MessageElement]

    @staticmethod
    def element_class_generator(target=MessageElement):
        for i in target.__subclasses__():
            yield i
            if i.__subclasses__():
                yield from MessageChain.element_class_generator(i)

    @staticmethod
    def search_element(name: str):
        for i in MessageChain.element_class_generator():
            if i.__name__ == name:
                return i

    @staticmethod
    def build_chain(obj: List[Union[dict, MessageElement]]):
        elements = []
        for i in obj:
            if isinstance(i, MessageElement):
                elements.append(i)
            elif isinstance(i, dict) and "type" in i:
                elements.append(MessageChain.search_element(i["type"]).parse_obj(i))
        return elements

    @classmethod
    def parse_obj(cls: Type["MessageChain"], obj: List[Union[dict, MessageElement]]) -> "MessageChain":
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

    def only_text(self) -> str:
        """获取消息链中的纯文字部分
        """
        return "".join(i.to_text() if i else "" for i in self.findall("Plain"))

    def findall(self, element_type: Union[str, Type[MessageElement]]) -> List[MessageElement]:
        if isinstance(element_type, str):
            element_type = MessageChain.search_element(element_type)
        return [i for i in self.__root__ if type(i) is element_type]

    def find(self, element_type: Union[str, Type[MessageElement]], index: int = 0) -> Union[bool, MessageElement]:
        """
        当消息链内有指定元素时返回该元素
        无则返回False
        """
        ele = self.findall(element_type)
        return False if not ele else ele[index]

    def has(self, element_type: Union[str, Type[MessageElement]]) -> bool:
        """
        当消息链内有指定元素时返回True
        无则返回False
        """
        ele = self.findall(element_type)
        return False if not ele else True

    def pop(self, index: int) -> MessageElement:
        return self.__root__.pop(index)

    def index(self, element_type: Union[str, Type[MessageElement]]) -> int:
        return self.__root__.index(self.find(element_type))

    def append(self, element: MessageElement) -> None:
        self.__root__.append(element)

    def extend(self, *elements: Union[MessageElement, List[MessageElement]]) -> None:
        element_list = []
        for ele in elements:
            if isinstance(ele, MessageElement):
                element_list.append(ele)
            else:
                element_list.extend(ele)
        self.__root__ += element_list

    def copy_self(self) -> "MessageChain":
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

    def __getitem__(self, index) -> MessageElement:
        return self.__root__[index]

    def __len__(self) -> int:
        return len(self.__root__)

    def startswith(self, string: str) -> bool:
        if not self.__root__:
            return False
        return self.to_text().startswith(string)

    def endswith(self, string: str) -> bool:
        if not self.__root__:
            return False
        return self.to_text().endswith(string)


_update_forward_refs()
