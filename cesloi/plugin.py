import os
from types import ModuleType
from typing import Optional, Dict, Union, Type, Callable
import importlib

from pydantic import BaseModel

from .delegatesystem import EventDelegate, TemplateEvent, Publisher
from .logger import Logger
from .command import Command


_module_target_dict: Dict[str, list] = {}


class CommandHandler(BaseModel):
    command: Command
    require_param_name: str = None,
    is_replace_message: bool = True

    def __init__(
            self,
            command: Command,
            require_param_name: Optional[str] = None,
            is_replace_message: bool = True
    ):
        super().__init__(
            command=command,
            is_replace_message=is_replace_message
        )
        self.require_param_name = require_param_name

    class Config:
        arbitrary_types_allowed = True


class TemplatePlugin:
    module: ModuleType
    name: str
    usage: str
    is_close: bool = False

    def __init__(self, module, name:Optional[str] = None, usage: Optional[str] = None):
        if hasattr(module.__init__, "__annotations__"):
            module.__init__(**module.__init__.__annotations__)
        self.module = module
        self.name = name or ""
        self.usage = usage or ""


class Bellidin:
    """插件管理器

     - set_bellidin: 初始化管理器，通常不需要管
     - install_plugin: 载入单个模块，需要提供相对路径
     - install_plugins: 载入文件夹下的所有模块，需要提供相对路径
    """
    ignore = ["__init__.py", "__pycache__"]
    _modules: Dict[str, "TemplatePlugin"] = {}
    current_module_name: str
    delegate: EventDelegate
    logger: Logger.logger
    plugins_dir: str

    @classmethod
    def model_register(
            cls,
            event: Union[str, Type[TemplateEvent]],
            *,
            match_command: Optional[CommandHandler] = None
    ):
        if not cls.delegate:
            raise RuntimeError("Delegate didn't existed!")
        if isinstance(event, str):
            name = event
            event = cls.delegate.search_event(event)
            if not event:
                raise Exception(name + " cannot found!")

        def register_wrapper(func: Callable):
            from .delegatesystem.entities.subsciber import SubscriberHandler
            subscriber = SubscriberHandler().set(**match_command.dict())(func) if match_command else SubscriberHandler().set()(func)
            temp_publisher = cls.delegate.search_publisher(event)
            if not temp_publisher:
                cls.delegate.publisher_list.append(Publisher(subscriber, bind_event=event))
            else:
                if subscriber.name not in temp_publisher.subscribers_names():
                    temp_publisher.subscribers.append(subscriber)
                else:
                    raise ValueError(f"Function \"{subscriber.name}\" for {event.__name__} has already registered!")
            if cls.current_module_name not in _module_target_dict:
                _module_target_dict[cls.current_module_name] = [[event, subscriber]]
            else:
                _module_target_dict[cls.current_module_name].append([event, subscriber])
            return func

        return register_wrapper

    @classmethod
    def set_bellidin(cls, delegate, logger):
        cls.delegate = delegate
        cls.logger = logger
        cls.plugins_dir = ""
        return cls

    @classmethod
    def get_delegate(cls):
        return cls.delegate

    @classmethod
    def install_plugin(cls, modules_name: str):
        try:
            cls.current_module_name = modules_name
            module = importlib.import_module(modules_name, modules_name)
            name = getattr(module, '__name__', None)
            usage = getattr(module, '__usage', None)
            cls._modules[modules_name] = TemplatePlugin(module, name, usage)
            cls.logger.debug(f"plugin: {module.__name__} is installed")
            return True
        except Exception as e:
            cls.logger.exception(e)
            return False

    @classmethod
    def install_plugins(cls, plugin_dir: str):
        cls.plugins_dir = plugin_dir
        plugin_count = 0
        for module in os.listdir(plugin_dir):
            if module in cls.ignore:
                continue
            if os.path.isdir(module):
                cls.install_plugin(f"{plugin_dir.replace('/','.')}.{module}")
                plugin_count += 1
            else:
                cls.install_plugin(f"{plugin_dir.replace('/','.')}.{module.split('.')[0]}")
                plugin_count += 1
        cls.logger.info(f"{plugin_count} plugin have been installed")
        return plugin_count

    @classmethod
    def get_plugins(cls):
        return cls._modules

    @classmethod
    def uninstall_plugins(cls, *args, **kwargs):
        plugin_count = 0
        for module_name in cls._modules:
            targets = _module_target_dict[module_name]
            for target in targets:
                t_publisher = cls.delegate.search_publisher(target[0])
                t_publisher.remove_subscriber(target[1])
                if not t_publisher.subscribers:
                    cls.delegate.remove_publisher(t_publisher)
            _module_target_dict[module_name].clear()
            module = cls._modules[module_name].module
            if hasattr(module, "__end__"):
                try:
                    module.__end__(
                        *args, **module.__end__.__annotations__
                    )
                except Exception as e:
                    cls.logger.exception(e)
                    module.is_close = False
                else:
                    cls.logger.debug(f"plugin: {module.__name__} is uninstalled")
                    module.is_close = True
            plugin_count += 1
        cls._modules.clear()
        cls.logger.info(f"{plugin_count} plugins have been uninstalled successfully")
        return plugin_count

    @classmethod
    def uninstall_plugin(cls, module_name: str, *args, **kwargs):
        try:
            if module_name in cls._modules:
                targets = _module_target_dict[module_name]
                for target in targets:
                    t_publisher = cls.delegate.search_publisher(target[0])
                    t_publisher.remove_subscriber(target[1])
                    if not t_publisher.subscribers:
                        cls.delegate.remove_publisher(t_publisher)
                module = cls._modules[module_name].module
                if hasattr(module, "__end__"):
                    try:
                        module.__end__(
                            *args, **module.__end__.__annotations__
                        )
                    except Exception as e:
                        cls.logger.exception(e)
                        module.is_close = False
                    else:
                        cls.logger.debug(f"plugin: {module.__name__} is uninstalled")
                        module.is_close = True
            else:
                raise ValueError(f"No such plugin named {module_name}")
        except Exception as e:
            cls.logger.debug(e)
            pass

    @classmethod
    def reload_plugins(cls, new_plugins_dir: Optional[str] = None):
        try:
            if new_plugins_dir:
                cls.uninstall_plugins(cls.plugins_dir)
                cls.plugins_dir = new_plugins_dir
                cls.logger.info(f"reload plugins at {new_plugins_dir}")
                return cls.install_plugins(new_plugins_dir)
            else:
                cls.logger.info(f"reload plugins at {cls.plugins_dir}")
                plugin_count = 0
                for module_name in cls._modules:
                    targets = _module_target_dict[module_name]
                    for target in targets:
                        t_publisher = cls.delegate.search_publisher(target[0])
                        t_publisher.remove_subscriber(target[1])
                        if not t_publisher.subscribers:
                            cls.delegate.remove_publisher(t_publisher)
                    _module_target_dict[module_name].clear()
                    module = cls._modules[module_name].module
                    importlib.reload(module)
                    plugin_count += 1

                cls._modules.clear()
                cls.logger.info(f"{plugin_count} plugins have been reload successfully")
                return plugin_count
        except Exception as e:
            cls.logger.exception(e)
            pass
