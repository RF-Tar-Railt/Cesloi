from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Permission(Enum):
    """描述群成员在群组中的权限"""

    Member = "MEMBER"  # 普通成员
    Administrator = "ADMINISTRATOR"  # 管理员
    Owner = "OWNER"  # 群主


class Equipment(Enum):
    """客户端的设备名称信息"""

    Mobile = "MOBILE"  # 手机
    Windows = "WINDOWS"  # win电脑
    MacOS = "MACOS"  # mac电脑


class Friend(BaseModel):
    """好友的信息."""

    id: int
    nickname: str
    remark: Optional[str]


class Group(BaseModel):
    id: int
    name: str
    accountPerm: Permission = Field(..., alias="permission")

    def avatar(self):
        return f'https://p.qlogo.cn/gh/{self.id}/{self.id}'


class Member(BaseModel):
    id: int
    name: str = Field(..., alias="memberName")
    permission: Permission
    specialTitle: Optional[str] = None
    joinTimestamp: Optional[int] = None
    lastSpeakTimestamp: Optional[int] = None
    muteTimeRemaining: Optional[int] = None
    group: Group

    def avatar(self):
        return f'https://q4.qlogo.cn/g?b=qq&nk={self.id}&s=140'


class GroupConfig(BaseModel):
    """描述群组各项功能的设置."""

    name: str
    announcement: str
    confessTalk: bool
    allowMemberInvite: bool
    autoApprove: bool
    anonymousChat: bool

    class Config:
        allow_mutation = True


class MemberInfo(BaseModel):
    """描述群组成员的各项功能的设置（需要有相关限权）."""

    id: int
    name: str = Field("", alias="memberName")
    specialTitle: str = ""
    permission: Permission
    joinTimestamp: Optional[int] = None
    lastSpeakTimestamp: Optional[int] = None
    muteTimeRemaining: Optional[int] = None
    group: Group

    class Config:
        allow_mutation = True

    def avatar(self):
        return f'https://q4.qlogo.cn/g?b=qq&nk={self.id}&s=140'


class Client(BaseModel):
    id: int
    platform: Equipment
