import json as JSON
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING, Union, List
from base64 import b64decode, b64encode
from ..context import bot_application
import aiohttp
from pydantic import BaseModel, validator, Field, BaseConfig, Extra
from abc import ABC, abstractmethod
if TYPE_CHECKING:
    from .messageChain import MessageChain
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny, DictStrAny


class ElementModel(BaseModel):
    class Config(BaseConfig):
        extra = Extra.allow


class MessageElement(ABC, ElementModel):
    type: str

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))

    @abstractmethod
    def to_serialization(self) -> str:
        """将元素转为可序列化的字符串"""

    @staticmethod
    @abstractmethod
    def from_json(json: Dict):
        """将json转换为元素"""

    def to_text(self) -> str:
        return ""


class MediaElement(MessageElement):
    url: Optional[str] = None
    path: Optional[Union[Path, str]] = None
    base64: Optional[str] = None

    async def get_bytes(self) -> bytes:
        if self.url and not self.base64:
            async with aiohttp.request("GET", self.url) as response:
                if response.status != 200:
                    raise ConnectionError(response.status, await response.text())
                data = await response.content.readexactly(response.content_length)
                self.base64 = str(b64encode(data))
                return data
        if self.base64:
            return b64decode(self.base64)

    def dict(
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "DictStrAny":
        return super().dict(
            by_alias=True
        )
    @staticmethod
    @abstractmethod
    def from_local_path(path: Union[Path, str]):
        pass

    @classmethod
    @abstractmethod
    def from_url(cls, path: str):
        pass

    @staticmethod
    @abstractmethod
    def from_bytes(data: bytes):
        pass


class Source(MessageElement):
    """表示消息在一个特定聊天区域内的唯一标识"""
    type: str = "Source"
    id: int
    time: int

    def to_serialization(self) -> str:
        return f"[mirai:source:{self.id},{self.time}]"

    @staticmethod
    def from_json(json: Dict) -> "Source":
        return Source.parse_obj(json)


class Quote(MessageElement):
    """表示消息中回复其他消息/用户的部分, 通常包含一个完整的消息链(`origin` 属性)"""
    type: str = "Quote"
    id: int
    groupId: int
    senderId: int
    targetId: int
    origin: "MessageChain"

    @validator("origin", pre=True, allow_reuse=True)
    def _(cls, v):
        from .messageChain import MessageChain
        return MessageChain(v)

    def to_serialization(self) -> str:
        return f" [mirai:quote:{self.id}]"

    @staticmethod
    def from_json(json: Dict) -> "Quote":
        return Quote.parse_obj(json)


class Plain(MessageElement):
    type: str = "Plain"
    text: str

    def __init__(self, text: str, **kwargs) -> None:
        """实例化一个 Plain 消息元素, 用于承载消息中的文字.

        Args:
            text (str): 元素所包含的文字
        """
        super().__init__(text=text, **kwargs)

    def to_text(self):
        return self.text

    def to_serialization(self) -> str:
        return self.text

    @staticmethod
    def from_json(json: Dict) -> "Plain":
        return Plain.parse_obj(json)


class At(MessageElement):
    """该消息元素用于承载消息中用于提醒/呼唤特定用户的部分."""

    type: str = "At"
    target: int
    display: Optional[str] = None

    def __init__(self, target: int, **kwargs) -> None:
        """实例化一个 At 消息元素, 用于承载消息中用于提醒/呼唤特定用户的部分.

        Args:
            target (int): 需要提醒/呼唤的特定用户的 QQ 号(或者说 id.)
        """
        super().__init__(target=target, **kwargs)

    def to_text(self) -> str:
        return str(self.display) if self.display else f"@{self.target}"

    def to_serialization(self) -> str:
        return f"[mirai:at:{self.target},{self.display}]"

    @staticmethod
    def from_json(json: Dict) -> "At":
        return At.parse_obj(json)


class AtAll(MessageElement):
    """该消息元素用于群组中的管理员提醒群组中的所有成员"""
    type: str = "AtAll"

    def to_text(self) -> str:
        return "@全体成员"

    def to_serialization(self) -> str:
        return "[mirai:atall]"

    @staticmethod
    def from_json(json: Dict):
        return AtAll()


class Face(MessageElement):
    """表示消息中所附带的表情, 这些表情大多都是聊天工具内置的."""
    type: str = "Face"
    faceId: int
    name: Optional[str] = None

    def to_text(self) -> str:
        return "[表情]"

    def to_serialization(self) -> str:
        return f"[mirai:face:{self.faceId}]"

    @staticmethod
    def from_json(json: Dict) -> "Face":
        return Face.parse_obj(json)


class Xml(MessageElement):
    type = "Xml"
    xml: str

    def __init__(self, xml, *_, **__) -> None:
        super().__init__(xml=xml)

    def to_text(self) -> str:
        return "[XML消息]"

    def to_serialization(self) -> str:
        return f"[mirai:xml:{self.xml}]"

    @staticmethod
    def from_json(json: Dict):
        return Xml.parse_obj(json)


class Json(MessageElement):
    type = "Json"
    Json: str = Field(..., alias="json")

    def __init__(self, json: Union[dict, str], **kwargs) -> None:
        if isinstance(json, dict):
            json = JSON.dumps(json)
        super().__init__(json=json, **kwargs)

    def dict(self, *args, **kwargs):
        return super().dict(*args, **({**kwargs, "by_alias": True}))

    def to_text(self) -> str:
        return "[JSON消息]"

    def to_serialization(self) -> str:
        return f"[mirai:json:{self.Json}]"

    @staticmethod
    def from_json(json: Dict):
        return Json.parse_obj(json)


class App(MessageElement):
    type = "App"
    content: str

    def to_text(self) -> str:
        return "[APP消息]"

    def to_serialization(self) -> str:
        return f"[mirai:app:{self.content}]"

    @staticmethod
    def from_json(json: Dict):
        return App.parse_obj(json)


class PokeMethods(Enum):
    ChuoYiChuo = "ChuoYiChuo"
    BiXin = "BiXin"
    DianZan = "DianZan"
    XinSui = "XinSui"
    LiuLiuLiu = "LiuLiuLiu"
    FangDaZhao = "FangDaZhao"
    BaoBeiQiu = "BaoBeiQiu"
    Rose = "Rose"
    ZhaoHuanShu = "ZhaoHuanShu"
    RangNiPi = "RangNiPi"
    JeiYin = "JeiYin"
    ShouLei = "ShouLei"
    GouYin = "GouYin"
    ZhuaYiXia = "ZhuaYiXia"
    SuiPing = "SuiPing"
    QiaoMen = "QiaoMen"


class Poke(MessageElement):
    type = "Poke"
    name: PokeMethods

    def to_text(self) -> str:
        return f"[戳一戳:{self.name}]"

    def to_serialization(self) -> str:
        return f"[mirai:poke:{self.name}]"

    @staticmethod
    def from_json(json: Dict):
        return Poke.parse_obj(json)


class Dice(MessageElement):
    type = "Dice"
    value: int

    def to_text(self) -> str:
        return f"[骰子:{self.value}]"

    def to_serialization(self) -> str:
        return f"[mirai:dice:{self.value}]"

    @staticmethod
    def from_json(json: Dict):
        return Dice.parse_obj(json)


class File(MessageElement):
    type = "File"
    file_id: str
    name: str
    size: int

    def to_text(self) -> str:
        return f'[文件:{self.name}]'

    def to_serialization(self) -> str:
        return f'[mirai:file:{self.name}]'

    @staticmethod
    def from_json(json: Dict):
        return File.parse_obj(json)


class ImageType(Enum):
    Friend = "Friend"
    Group = "Group"
    Temp = "Temp"
    Unknown = "Unknown"


class Image(MediaElement):
    """该消息元素用于承载消息中所附带的图片."""
    type = "Image"
    imageId: Optional[str] = None
    url: Optional[str] = None
    path: Optional[Union[Path, str]] = None
    base64: Optional[str] = None

    def __init__(
            self,
            imageId: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[Path, str]] = None,
            base64: Optional[str] = None,
            **kwargs
    ):
        super().__init__(
            imageId=imageId,
            path=path,
            url=url,
            base64=base64,
            **kwargs
        )

    def to_text(self) -> str:
        return "[图片]"

    def to_serialization(self) -> str:
        return f"[mirai:image:{self.imageId}]"

    @staticmethod
    def from_json(json: Dict):
        return Image.parse_obj(json)

    @staticmethod
    def from_local_path(path: Union[Path, str]):
        if isinstance(path, str):
            path = Path(path)
        bot = bot_application.get()
        if not path.exists():
            raise FileNotFoundError(path)
        return bot.upload_image(path.read_bytes())

    @classmethod
    def from_url(cls, url: str):
        bot = bot_application.get()
        return bot.upload_image(cls(url=url).get_bytes())

    @staticmethod
    def from_bytes(data: bytes):
        bot = bot_application.get()
        return bot.upload_image(data)


class FlashImage(Image):
    """该消息元素用于承载消息中所附带的图片."""
    type = "FlashImage"

    def __init__(
            self,
            imageId: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[Path, str]] = None,
            base64: Optional[str] = None,
            **kwargs
    ):
        super().__init__(
            imageId=imageId,
            path=path,
            url=url,
            base64=base64,
            **kwargs
        )

    def to_text(self) -> str:
        return "[闪照]"

    def to_serialization(self) -> str:
        return f"[mirai:flash:{self.imageId}]"

    @staticmethod
    def from_json(json: Dict):
        return FlashImage.parse_obj(json)

    @staticmethod
    def from_local_path(path: Union[Path, str]):
        if isinstance(path, str):
            path = Path(path)
        bot = bot_application.get()
        if not path.exists():
            raise FileNotFoundError(path)
        return bot.upload_image(path.read_bytes(), is_flash=True)

    @classmethod
    def from_url(cls, url: str):
        bot = bot_application.get()
        return bot.upload_image(cls(url=url).get_bytes(), is_flash=True)

    @staticmethod
    def from_bytes(data: bytes):
        bot = bot_application.get()
        return bot.upload_image(data, is_flash=True)


class Voice(MediaElement):
    type = "Voice"
    voiceId: Optional[str]
    length: Optional[int]

    def __init__(
            self,
            voiceId: Optional[str] = None,
            url: Optional[str] = None,
            path: Optional[Union[Path, str]] = None,
            base64: Optional[str] = None,
            **kwargs
    ):
        super().__init__(
            voiceId=voiceId,
            path=path,
            url=url,
            base64=base64,
            **kwargs
        )

    def to_text(self) -> str:
        return "[语音]"

    def to_serialization(self) -> str:
        return f"[mirai:voice:{self.voiceId}]"

    @staticmethod
    def from_json(json: Dict):
        return Voice.parse_obj(json)

    @staticmethod
    def from_local_path(path: Union[Path, str]):
        if isinstance(path, str):
            path = Path(path)
        bot = bot_application.get()
        if not path.exists():
            raise FileNotFoundError(path)
        return bot.upload_voice(path.read_bytes())

    @classmethod
    def from_url(cls, url: str):
        bot = bot_application.get()
        return bot.upload_voice(cls(url=url).get_bytes())

    @staticmethod
    def from_bytes(data: bytes):
        bot = bot_application.get()
        return bot.upload_voice(data)


class MusicShare(MessageElement):
    type = "MusicShare"
    kind: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    jumpUrl: Optional[str]
    pictureUrl: Optional[str]
    musicUrl: Optional[str]
    brief: Optional[str]

    def to_text(self) -> str:
        return f"[音乐分享:{self.title}]"

    def to_serialization(self) -> str:
        return f"[mirai:musicshare:{self.title}]"

    @staticmethod
    def from_json(json: Dict):
        return MusicShare.parse_obj(json)


class ForwardNode(BaseModel):
    """表示合并转发中的一个节点"""
    senderId: int
    time: int
    senderName: str
    messageChain: Optional["MessageChain"]
    messageId: Optional[int]


class Forward(MessageElement):
    """
    指示合并转发信息
    nodeList (List[ForwardNode]): 转发的消息节点
    """

    type = "Forward"
    nodeList: List[ForwardNode]

    def to_text(self) -> str:
        return f"[合并转发:共{len(self.nodeList)}条]"

    def to_serialization(self) -> str:
        return f"[mirai:forward:{self.nodeList}]"

    @staticmethod
    def from_json(json: Dict):
        return Forward.parse_obj(json)


def _update_forward_refs():
    from .messageChain import MessageChain

    Quote.update_forward_refs(MessageChain=MessageChain)
    ForwardNode.update_forward_refs(MessageChain=MessageChain)
