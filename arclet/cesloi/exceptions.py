class InvalidEventTypeDefinition(Exception):
    """不合法的事件类型定义."""


class InvalidVerifyKey(Exception):
    """无效的 verifyKey 或其配置."""


class AccountNotFound(Exception):
    """指定的Bot不存在"""


class InvalidSession(Exception):
    """Session失效或不存在"""


class UnVerifiedSession(Exception):
    """Session未认证(未激活)"""


class UnknownTarget(Exception):
    """发送消息目标不存在(指定对象不存在)"""


class AccountMuted(Exception):
    """Bot被禁言，指Bot当前无法向指定群发送消息."""


class MessageTooLong(Exception):
    """消息过长, 尝试分段发送或报告问题."""


class InvalidArgument(Exception):
    """错误的访问，如参数错误等."""


class UnknownError(Exception):
    """其他错误"""


class ParamsUnmatched(Exception):
    """一个 text 没有被任何参数匹配成功"""


class InvalidOptionName(Exception):
    """option或subcommand的名字中填入了非法的字符"""


class NullName(Exception):
    """命令的名称写入了空字符"""
