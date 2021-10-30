from pydantic import BaseModel


class TemplateParamsInserter(BaseModel):
    """
    参数插入模型
    """
    name: str

    @classmethod
    def get_param(cls):
        """该方法必须是 `classmethod`.

        该方法的返回值必须为实际元素数据.
        """
        pass
