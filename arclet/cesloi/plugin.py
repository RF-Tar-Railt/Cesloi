import os
import sys
from types import ModuleType
from typing import Optional, Dict, Union, Type, Callable, List
import importlib
from ..letoderea import EventSystem, TemplateEvent, EventDelegate, Publisher, Subscriber, Condition_T, \
    TemplateDecorator, search_event, event_class_generator
from .logger import Logger


class TemplatePlugin:
    module: ModuleType
    name: str
    usage: str
    is_close: bool = False

    def __init__(self, module, name: Optional[str] = None, usage: Optional[str] = None):
        if hasattr(module.__init__, "__annotations__"):
            module.__init__(**module.__init__.__annotations__)
        self.module = module
        self.name = name or ""
        self.usage = usage or ""


class Bellidin:
    """
    贝利丁(Bellidin), Cesloi的哥哥

    Cesloi的插件管理器
     - set_bellidin: 初始化管理器，通常不需要管
     - install_plugin: 载入单个模块，需要提供相对路径
     - install_plugins: 载入文件夹下的所有模块，需要提供相对路径
    """
    ignore = ["__init__.py", "__pycache__"]
    _modules: Dict[str, "TemplatePlugin"] = {}
    _module_target_dict: Dict[str, list] = {}
    current_module_name: str
    event_system: EventSystem
    logger: Logger.logger
    plugins_dir: str

    @classmethod
    def model_register(
            cls,
            event: Union[str, Type[TemplateEvent]],
            *,
            priority: int = 16,
            conditions: List[Condition_T] = None,
            decorators: List[TemplateDecorator] = None,
    ):
        if not cls.event_system:
            raise RuntimeError("Delegate didn't existed!")
        if isinstance(event, str):
            name = event
            event = search_event(event)
            if not event:
                raise Exception(name + " cannot found!")

        events = [event]
        events.extend(event_class_generator(event))
        conditions = conditions or []
        decorators = decorators or []

        def register_wrapper(func: Callable):
            subscriber = Subscriber(
                callable_target=func,
                decorators=decorators
            )
            for e in events:
                may_publishers = cls.event_system.get_publisher(e)
                _event_handler = EventDelegate(event=e)
                _event_handler += subscriber
                if not may_publishers:
                    cls.event_system.publisher_list.append(Publisher(priority, conditions, _event_handler))
                else:
                    for m_publisher in may_publishers:
                        if m_publisher.equal_conditions(conditions):
                            m_publisher += _event_handler
                            break
                    else:
                        cls.event_system.publisher_list.append(Publisher(priority, conditions, _event_handler))
            if cls.current_module_name not in cls._module_target_dict:
                cls._module_target_dict[cls.current_module_name] = [[event, subscriber]]
            else:
                cls._module_target_dict[cls.current_module_name].append([event, subscriber])
            return func

        return register_wrapper

    @classmethod
    def _uninstall_subscriber(cls, module_name):
        if cls._module_target_dict.get(module_name):
            targets = cls._module_target_dict[module_name]
            for event_type, subscriber in targets:
                t_publishers = cls.event_system.get_publisher(event_type)
                for pub in t_publishers:
                    pub.internal_delegate[event_type.__name__].subscribers.remove(subscriber)
                    if not pub.internal_delegate[event_type.__name__].subscribers:
                        pub.remove_delegate(event_type)
                        if not pub.internal_delegate:
                            cls.event_system.remove_publisher(pub)
            del cls._module_target_dict[module_name]

    @classmethod
    def set_bellidin(cls, event_system, logger):
        cls.event_system = event_system
        cls.logger = logger
        cls.plugins_dir = ""
        return cls

    @classmethod
    def get_delegate(cls):
        return cls.event_system

    @classmethod
    def install_plugin(cls, modules_name: str):
        try:
            cls.current_module_name = modules_name
            module = importlib.import_module(modules_name, modules_name)

            name = getattr(module, '__name__', None)
            usage = getattr(module, '__usage__', None)
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
                cls.install_plugin(f"{plugin_dir.replace('/', '.')}.{module}")
                plugin_count += 1
            else:
                cls.install_plugin(f"{plugin_dir.replace('/', '.')}.{module.split('.')[0]}")
                plugin_count += 1
        cls.logger.info(f"{plugin_count} plugin have been installed")
        return plugin_count

    @classmethod
    def get_plugins(cls):
        return cls._modules

    @classmethod
    def uninstall_plugins(cls, *args, **kwargs):
        plugin_count = 0
        _names = list(cls._modules.keys())
        for file in os.listdir(cls.plugins_dir):
            if file == "__pycache__":
                for pyc in os.listdir(cls.plugins_dir + "/__pycache__"):
                    os.remove(cls.plugins_dir + "/__pycache__/" + pyc)
        for module_name in _names:
            cls.logger.debug(f"plugin: {module_name} uninstalling")
            cls._uninstall_subscriber(module_name)
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
            del cls._modules[module_name]
            plugin_count += 1
            if sys.modules.get(module_name):
                del sys.modules[module_name]

        cls._modules.clear()
        cls.logger.info(f"{plugin_count} plugins have been uninstalled successfully")
        return plugin_count

    @classmethod
    def uninstall_plugin(cls, module_name: str, *args, **kwargs):
        try:
            if module_name in cls._modules:
                cls._uninstall_subscriber(module_name)
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
                del cls._modules[module_name]
                if sys.modules.get(module_name):
                    del sys.modules[module_name]
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
                cls.logger.info(f"reload plugins at \"./{new_plugins_dir}\"")
                return cls.install_plugins(new_plugins_dir)
            else:
                cls.logger.info(f"reload plugins at \"./{cls.plugins_dir}\"")
                plugin_count = 0
                _names = list(cls._modules.keys())
                for module_name in _names:
                    cls._uninstall_subscriber(module_name)
                    cls.current_module_name = module_name
                    importlib.invalidate_caches()
                    cls._modules[module_name].module = importlib.reload(cls._modules[module_name].module)
                    cls.logger.debug(f"plugin: {cls._modules[module_name].module.__name__} is reloaded")
                    plugin_count += 1

                cls.logger.info(f"{plugin_count} plugins have been reload successfully")
                return plugin_count
        except Exception as e:
            cls.logger.exception(e)
            pass
