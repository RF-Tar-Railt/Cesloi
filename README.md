# Cesloi for mirai-api-http
[![Licence](https://img.shields.io/github/license/RF-Tar-Railt/Cesloi)](https://github.com/RF-Tar-Railt/Cesloi/blob/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cesloi)](https://pypi.org/project/cesloi)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cesloi)](https://www.python.org/)

一个简易(?)，基于 [`mirai-api-http v2`](https://github.com/project-mirai/mirai-api-http) 的 Python SDK。

**本项目适用于 mirai-api-http 2.0 以上版本**。

项目仍处于开发阶段，部分内容可能会有较大改变

注: mirai-api-http 需要启用ws adapter和http adapter

## 安装
`pip install cesloi`

## 简单的开始
### 通常版本
```python
from cesloi.bot_client import Cesloi
from cesloi.model.relation import Friend
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.communicate_with_mah import BotSession
from cesloi.command import Command

bot = Cesloi(bot_session=BotSession(host="YourHost", account="YourQQ", verify_key="YourVerifyKey"))
sh = SubscriberHandler()

@bot.register("FriendMessage")
@sh.set(command=Command(["Hello"]))
async def test(app: Cesloi, friend: Friend):
    await app.send_with(friend, "Hello, World!")
    
bot.start()
```
### 使用插件的版本
In `main.py` :
```python
from cesloi.bot_client import Cesloi
from cesloi.communicate_with_mah import BotSession


bot = Cesloi(bot_session=BotSession(host="http://localhost:9080", account=2582049752, verify_key="INITKEYWylsVdbr"))
bot.install_plugins("test_plugins")
bot.start()
```
In `test_plugins/example_plugin.py` :
```python
from cesloi.bot_client import Cesloi
from cesloi.model.relation import Friend
from cesloi.delegatesystem.entities.subsciber import SubscriberHandler
from cesloi.command import Command
from cesloi.plugin import Bellidin as bd

sh = SubscriberHandler()

@bd.register("FriendMessage")
@sh.set(command=Command(["Hello"]))
async def test(app: Cesloi, friend: Friend):
    await app.send_with(friend, "Hello, World!")
```

## 未来开发计划
 - ~~CommandAnalysis， 一个抽象的命令/命令参数处理器~~ (已实现)
 - TimeScheduler， 一个根据时间选择是否执行目标函数的容器
 - ~~PluginManager， 不局限于在一个文件中运行方法~~ (已实现)

## 鸣谢&相关项目
> 这些项目也很棒, 去他们的项目页看看, 点个 `Star` 以鼓励他们的开发工作, 毕竟没有他们也没有 `Cesloi`.
> 
特别感谢 [`mamoe`](https://github.com/mamoe) 给我们带来这些精彩的项目:
 - [`mirai`](https://github.com/mamoe/mirai): 一个高性能, 高可扩展性的 QQ 协议库
 - [`mirai-console`](https://github.com/mamoe/mirai-console): 一个基于 `mirai` 开发的插件式可扩展开发平台
 - [`mirai-api-http`](https://github.com/project-mirai/mirai-api-http): 为本项目提供与 `mirai` 交互方式的 `mirai-console` 插件

[`GraiaProject`](https://github.com/GraiaProject) 下的项目:
 - [`Broadcast Control`](https://github.com/GraiaProject/BroadcastControl): 本项目关于参数解析与事件循环的的~~解剖~~学习对象。
 - [`Application`](https://github.com/GraiaProject/Application/): 本项目的通用功能的~~解剖~~学习与参考对象。
 - [`Ariadne`](https://github.com/GraiaProject/Ariadne/): 本项目关于网络部分的学习与参考对象。 


### 许可证

[`GNU AGPLv3`](https://choosealicense.com/licenses/agpl-3.0/) 是本项目的开源许可证.
