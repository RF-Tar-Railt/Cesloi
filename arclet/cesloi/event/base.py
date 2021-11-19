from arclet.letoderea.entities.event import TemplateEvent
from pydantic.class_validators import validator
from ..utils import Structured

from .inserter import ApplicationInserter, EventInserter


class MiraiEvent(Structured, TemplateEvent):
    type: str

    @classmethod
    @validator("type", allow_reuse=True)
    def type_limit(cls, v):
        if cls.type != v:
            raise Exception("{0}'s type must be '{1}', not '{2}'".format(cls.__name__, cls.type, v))
        return v

    class Config:
        extra = "ignore"


class EmptyEvent(MiraiEvent):

    def get_params(self):
        return self.param_export(
            ApplicationInserter,
            EventInserter
        )
