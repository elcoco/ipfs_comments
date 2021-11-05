#!/usr/bin/env python3

import logging
from pathlib import Path
from pprint import pprint

from core import plugin_manager


from plugins.ipfs.models import write_node, get_dag, load_node
from plugins.ipfs.models import CommentNode

import ipfshttpclient

logger = logging.getLogger('app')


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
        logger.debug(">>>> Root CID: "+ root.cid)

        return [c.get_json() for c in comments]


    def add_comment(self, site_id, blog_id, post_id, data):
        root = load_node('bafyreidenn7id6o6chduosfx2abpho6r5eko6s3owv4d6kn6dv3suexoiu')

        site = root.get_site(site_id)
        blog = site.get_blog(blog_id)
        post = blog.get_post(post_id)

        # keys should be lower case
        lower_data = { k.lower(): v for k,v in data.items()}

        with ipfshttpclient.connect() as client:
            comment = CommentNode(client, **lower_data)
            comment.write()

        post.add_link("Comments", comment)

        root.write_tree()
                              
        logger.debug(">>>> Root CID: "+ root.cid)




        return comment.get_json()
         



def register():
    plugin = Plugin()
    plugin_manager.subscribe_hook('get_post_comments', 'ipfs', plugin.get_post_comments)
    plugin_manager.subscribe_hook('add_comment', 'ipfs', plugin.add_comment)
