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
        self.root_node = write_node()

    def get_post_comments(self, site_id, blog_id, post_id):
        #for s in self.root_node["Sites"]:
        #    if s["Name"] == site_id:
        #        break
        #else:
        #    return None

        #for b in s['Blogs']:
        #    if s["Name"] == blog_id:
        #        break
        #else:
        #    return None

        #for p in b['Posts']:
        #    if s["Name"] == post_id:
        #        break
        #else:
        #    return None
        root = load_node('bafyreiddyixgxp25fnesku7pgfkbjihkt4xkdflpzvihqvdcafvtxilzs4')

        comments = root.get_comments(site_id, blog_id, post_id)
        if not comments:
            return

        for c in comments:
            print(c.name)

        return [c.get_json() for c in comments]

        

        #s = next(iter([s for s in self.root_node.json["Sites"] if s['Name'] == site_id]))
        #site = get_dag(s[site_id]['/'])
        #b = next(iter([b for b in site.json["Blogs"] if s['Name'] == blog_id]))
        #blog = get_dag(b[blog_id]['/'])
        #p = next(iter([p for p in blog.json["Posts"] if s['Name'] == post_id]))
        #post = get_dag(p[post_id]['/'])
        #print(post.json)
        #return site.json





    def get_comments(self, site_id, blog_id, post_id):
        return self.root_node.json



def register():
    plugin = Plugin()
    plugin_manager.register('ipfs', plugin)
    plugin_manager.subscribe_hook('get_post_comments', 'ipfs', plugin.get_post_comments)
