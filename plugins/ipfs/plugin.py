#!/usr/bin/env python3

import logging
from pathlib import Path
from pprint import pprint

from core import plugin_manager

from plugins.ipfs.models import write_node, get_dag, load_node

logger = logging.getLogger('')


class Plugin():
    def __init__(self):
        self.name = 'ipfs'
        #self.root_node = write_node()

    def get_post_comments(self, site_id, blog_id, post_id):
        root = load_node('bafyreidenn7id6o6chduosfx2abpho6r5eko6s3owv4d6kn6dv3suexoiu')

        comments = root.get_comments(site_id, blog_id, post_id)
        if not comments:
            return

        root.write_tree()
        print(">>>> Root CID: ", root.cid)

        return [c.get_json() for c in comments]







    def get_comments(self, site_id, blog_id, post_id):
        return self.root_node.json



def register():
    plugin = Plugin()
    plugin_manager.register('ipfs', plugin)
    plugin_manager.subscribe_hook('get_post_comments', 'ipfs', plugin.get_post_comments)
