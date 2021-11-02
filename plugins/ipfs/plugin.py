#!/usr/bin/env python3

import logging
from pathlib import Path

from core import plugin_manager

logger = logging.getLogger('')


class Plugin():
    def __init__(self):
        self.name = 'ipfs'

    def get_comments(self, site_id, blog_id, post_id):
        print(">>>>>>>>>>>diskobever")


def register():
    plugin = Plugin()
    plugin_manager.register('ipfs', plugin)
    plugin_manager.subscribe_hook('get_comments', 'ipfs', plugin.get_comments)
