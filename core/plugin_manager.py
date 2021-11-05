#!/usr/bin/env python3

# TODO print out a mapping of subs

import logging

from dataclasses import dataclass, field
from typing import Any, Callable, List, Dict
from pathlib import Path
import importlib
from enum import Enum, auto

logger = logging.getLogger('app')


class PluginException(Exception):
    pass

class Policy(Enum):
    """ Enum defines the run policy options for Hook class """
    FIRST = auto()  # return the first callback that returns a positive
    ALL   = auto()


class ModuleInterface:
    """Represents a plugin interface. A plugin has a single register function."""

    @staticmethod
    def register() -> None:
        """Register the necessary items in the game character factory."""


@dataclass
class Hook():
    """ Hook class represents hook that can be registered and subscribed to """
    name: str
    run_policy: Policy = Policy.ALL
    subscribers: Dict[str,Callable] = field(default_factory=dict)

    def add_subscriber(self, name: str, callback: Callable):
        self.subscribers[name] = callback

    def run(self, *args, **kwargs):
        for name, callback in self.subscribers.items():
            ret = callback(*args, **kwargs)

            if self.run_policy == Policy.FIRST:
                if ret != None:
                    return ret
            elif self.run_policy == Policy.ALL:
                continue


class PluginManager():
    """ Keep track of plugins, create instances, returns appropriate objects """

    def __init__(self):
        self._plugins = {}
        self._hooks = {}

    @property
    def plugins(self):
        return self._plugins.values()

    def register(self, name, obj):
        """ Register a plugin """
        self._plugins[name] = obj

    def register_hook(self, name, run_policy: Policy = Policy.ALL):
        """ Enable the host to create a new hook """
        self._hooks[name] = Hook(name, run_policy=run_policy)

    def subscribe_hook(self, hook_name, sub_name, callback):
        """ Enable a plugin to subscribe to a hook """

        if (hook := self._hooks.get(hook_name, None)):
            hook.add_subscriber(sub_name, callback)
        else:
            raise PluginException("Plugin tried to subscribe to nonexisting hook")

    def load_plugins(self, plugin_list: List[str]):
        """ Do the importing """
        for name in plugin_list:
            plugin = importlib.import_module(f"plugins.{name}.plugin")
            plugin.register()

    def run_hook(self, name, *args, **kwargs):
        """ Execute the callbacks from the hooks """
        hook = self._hooks.get(name, None)
        if hook == None:
            raise PluginException(f"Error, Failed to run hook, {name} doesn't exist")
        return hook.run(*args, **kwargs)

    def print_hooks(self):
        """ Print out all hooks and its subscribers """
        for name, hook in self._hooks.items():
            print(f"hook: {name}")
            for subscriber, callback in hook.subscribers.items():
                print(f"    {subscriber}")
