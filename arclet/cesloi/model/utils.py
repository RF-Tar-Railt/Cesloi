import aiohttp
from pathlib import Path
from .relation import Group, Friend
from typing import Optional, Literal, Union
from pydantic import BaseModel


class BotMessage(BaseModel):
    messageId: int


class Profile(BaseModel):
    nickname: str
    email: Optional[str]
    age: Optional[int]
    level: int
    sign: str
    sex: Literal["UNKNOWN", "MALE", "FEMALE"]


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
        if self.is_file:
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
        else:
            return


FileInfo.update_forward_refs(FileInfo=FileInfo)
