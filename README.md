<div align="center"> 
  
# Cesloi
  
</div>

## 简介

[![Licence](https://img.shields.io/github/license/RF-Tar-Railt/Cesloi)](https://github.com/RF-Tar-Railt/Cesloi/blob/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cesloi)](https://pypi.org/project/cesloi)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cesloi)](https://www.python.org/)

一个简易(?)，基于 [`mirai-api-http v2`](https://github.com/project-mirai/mirai-api-http) 的 Python SDK。

**本项目适用于 mirai-api-http 2.0 以上版本**。

项目仍处于开发阶段，部分内容可能会有较大改变

注: mirai-api-http 需要启用ws adapter和http adapter

## 文档

[Cesloi暂时的文档](https://github.com/RF-Tar-Railt/Cesloi/wiki)

## 安装
`pip install cesloi`

## 简单的开始
### 通常版本
```python
from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.model.relation import Friend
from arclet.cesloi.communicate_with_mah import BotSession
from arclet.cesloi.message.alconna import Alconna, Arpamar, AlconnaParser

bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=1234567890, verify_key="INITKEYWylsVdbr"),
             debug=False)

@bot.register(
    "FriendMessage",
    decorators=[AlconnaParser(alconna=Alconna(command="Hello"))]
)
async def test(app: Cesloi, friend: Friend, result: Arpamar):
    await app.send_with(friend, "Hello, World!")
    if result.matched:
        await app.send_with(friend,nudge=True)
    
bot.start()
```
### 使用插件的版本
In `main.py` :
```python
from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.communicate_with_mah import BotSession


bot = Cesloi(bot_session=BotSession(host="http://localhost:8080", account=1234567890, verify_key="INITKEYWylsVdbr"), debug=False)
bot.install_plugins("test_plugins")
bot.start()

```
In `test_plugins/example_plugin.py` :
```python
from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.model.relation import Friend
from arclet.cesloi.message.alconna import Alconna, Arpamar, AlconnaParser
from arclet.cesloi.plugin import Bellidin as bd


@bd.model_register(
    "FriendMessage",
    decorators=[AlconnaParser(alconna=Alconna(command="Hello"))]
)
async def test(app: Cesloi, friend: Friend, result: Arpamar):
    await app.send_with(friend, "Hello, World!")
    if result.matched:
        await app.send_with(friend,nudge=True)
```

## 未来开发计划
**一期计划**
 - ~~CommandAnalysis， 一个抽象的命令/命令参数处理器~~ (已实现)
 - ~~TimeScheduler， 一个根据时间选择是否执行目标函数的容器~~(已实现)
 - ~~PluginManager， 不局限于在一个文件中运行方法~~ (已实现)

**二期计划**
 - ~~Interrupt, 中断处理~~ (已实现)
 - ~~Decorator，用户自定义的处理器~~ (已实现)

**三期计划**
 - 主题框架再封装
 - 完善文档

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
