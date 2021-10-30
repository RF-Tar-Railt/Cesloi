from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel


class Equipment(Enum):
    """客户端的设备名称信息"""

    Mobile = "MOBILE"  # 手机
    Windows = "WINDOWS"  # win电脑
    MacOS = "MACOS"  # mac电脑


class BotMessage(BaseModel):
    messageId: int


class Friend(BaseModel):
    """好友的信息."""

    id: int
    nickname: str
    remark: Optional[str]


class Client(BaseModel):
    id: int
    platform: Equipment


class Profile(BaseModel):
    nickname: str
    email: Optional[str]
    age: Optional[int]
    level: int
    sign: str
    sex: Literal["UNKNOWN", "MALE", "FEMALE"]
