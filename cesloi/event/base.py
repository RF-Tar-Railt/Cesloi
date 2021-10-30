from cesloi.delegatesystem import TemplateEvent
from pydantic.class_validators import validator

from cesloi.delegatesystem.entities.event import ParamsAnalysis
from .inserter import ApplicationInserter, EventInserter


class MiraiEvent(TemplateEvent):
    type: str

    @validator("type", allow_reuse=True)
    def type_limit(cls, v):
        if cls.type != v:
            raise Exception("{0}'s type must be '{1}', not '{2}'".format(cls.__name__, cls.type, v))
        return v

    class Config:
        extra = "ignore"


class EmptyEvent(TemplateEvent):
    def get_params(self, params):
        return ParamsAnalysis(
            ApplicationInserter,
            EventInserter
        ).error_param_check(params)