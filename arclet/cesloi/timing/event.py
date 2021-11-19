from ...letoderea.entities.event import TemplateEvent, ParamRet


class ScheduleTaskEvent(TemplateEvent):

    @classmethod
    def get_params(cls) -> ParamRet:
        return cls.param_export(
        )
