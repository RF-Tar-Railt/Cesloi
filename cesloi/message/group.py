from enum import Enum
from pathlib import Path
from typing import Optional, Union
import aiohttp
from pydantic import BaseModel, Field

from cesloi.message import Friend


class Permission(Enum):
    """描述群成员在群组中的权限"""

    Member = "MEMBER"  # 普通成员
    Administrator = "ADMINISTRATOR"  # 管理员
    Owner = "OWNER"  # 群主


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

    name: str = ""
    specialTitle: str = ""

    class Config:
        allow_mutation = True


class DownloadInfo(BaseModel):
    """群组文件的下载信息"""
    download_times: Optional[int]
    uploader_id: Optional[int]
    upload_time: Optional[int]
    last_modify_time: Optional[int]

    url: Optional[str] = None
    sha1: Optional[str] = None
    md5: Optional[str] = None


class FileInfo(BaseModel):
    """描述群组文件的有关状态"""

    name: Optional[str] = None
    id: Optional[str] = None
    path: Optional[str] = None
    parent: Optional["FileInfo"] = None
    contact: Optional[Union[Group, Friend]] = None
    is_file: Optional[bool] = None
    is_directory: Optional[bool] = None
    downloadInfo: Optional[DownloadInfo] = None

    async def save_file(self, save_path: Union[Path, str]) -> None:
        """
        该方法不返回文件的二进制数据
        """
        if isinstance(save_path, str):
            save_path = Path(save_path)
        if not self.downloadInfo:
            raise AttributeError("cannot download")
        try:
            with save_path.open("wb") as f_obj:
                async with aiohttp.request("GET", self.downloadInfo.url) as resp:
                    async for result in resp.content:
                        f_obj.write(result)
        except Exception as e:
            save_path.unlink()
            raise e


FileInfo.update_forward_refs(FileInfo=FileInfo)
