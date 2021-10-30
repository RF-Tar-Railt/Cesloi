from typing import Dict, List, Any
from pydantic.main import BaseModel
import functools
from typing import Callable
from .paramsInserter import TemplateParamsInserter


class TemplateEvent(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def get_params(self, params) -> Dict[str, Any]:
        """该方法可以是 `classmethod` 亦或是普通的方法/函数.

        唯一的要求是该方法的返回值必须为装有参数名—实际元素数据的字典.

        Args:
            params: 调用的函数的参数字典
        """
        return ParamsAnalysis().error_param_check(
            params,
        )


def extra_params_insert(func: Callable[[Dict], Dict]):
    """
    额外参数插入函数，会根据事件提供的额外参数插入器以及函数的参数列表进行相应的参数插入
    """
    @functools.wraps(func)
    def wrapper(self: "ParamsAnalysis", *args, **kwargs):
        for inserter in self.ParamsInserterList:
            param = inserter.get_param()
            if param.__class__ in list(map(lambda x: x[0], list(args[0].values()))):
                kwargs[param.__class__.__name__] = param
        return func(self, *args, **kwargs)
    return wrapper


class ParamsAnalysis:
    ParamsInserterList: List[TemplateParamsInserter]

    def __init__(self, *extra_param_inserter):
        """事件相关的参数分析模型

        Args:
            extra_param_inserter: 可提供的额外参数插入器,该插入器应继承自TemplateParamsInserter
        """
        self.ParamsInserterList = list(extra_param_inserter)

    @extra_params_insert
    def error_param_check(self, params, **kwargs):
        """
        将调用函数提供的参数字典与事件提供的参数字典进行比对，并返回正确的参数字典

        Args:
            params: 调用的函数的参数字典

            kwargs: 该事件可传入的参数字典,以” 类型 = 实际参数 “方式写入
        :return: 函数需要的参数字典
        """
        arguments_dict = {}
        for k, v in params.items():
            if v[0].__name__ in kwargs.keys():
                if isinstance(kwargs[v[0].__name__], Dict):
                    arguments_dict[k] = kwargs[v[0].__name__][v[1]]
                else:
                    arguments_dict[k] = kwargs[v[0].__name__]
            elif v[1] is not None:
                arguments_dict[k] = v[1]
        if len(params.items()) > len(arguments_dict.items()):
            raise ValueError(
                "Unexpected Extra Argument: \n" +
                "".join(map(
                    lambda x, y: "{0}:{1}, ".format(x, y[0].__name__)
                    if x not in arguments_dict else "", params.keys(), params.values()
                ))
            )
        return arguments_dict
