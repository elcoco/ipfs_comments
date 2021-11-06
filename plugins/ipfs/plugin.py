#!/usr/bin/env python3

import logging
from pathlib import Path
from pprint import pprint
import datetime

from core import plugin_manager


from plugins.ipfs.models import load_tree
from plugins.ipfs.models import CommentNode

import ipfshttpclient

logger = logging.getLogger('app')


class Plugin():
    def __init__(self):
        self.name = 'ipfs'

        # TODO read root_cid from disk and keep on writing at any update
        self.root_cid = 'bafyreiblkpfc3w7wyd5b4s2xfbwybqo4pct52ups47lvnadi2tbv5cxb2e'

    def get_comments(self, site_id, blog_id, post_id):
        root = load_tree(self.root_cid)

        comments = root.get_comments(site_id, blog_id, post_id)
        if not comments:
            return

        root.write_tree()
        logger.debug(">>>> Root CID: "+ root.cid)

        return [c.get_json() for c in comments]

    def add_comment(self, site_id, blog_id, post_id, data):
        # read full tree from IPFS and create model
        root = load_tree(self.root_cid)

        # try to find the post where the comment should be added to
        site = root.get_site(site_id)
        blog = site.get_blog(blog_id)
        post = blog.get_post(post_id)

        # create and write comment to IPFS
        with ipfshttpclient.connect() as client:
            data["datetime"] = str(datetime.datetime.utcnow())
            comment = CommentNode(client, **data, parent=post)
            comment.write()

        # add comment to post and write branch up to the root node
        post.add_link("comments", comment)
        comment.write_branch()
                              
        self.root_cid = root.cid
        logger.debug(">>>> Root CID: "+ root.cid)
        return comment.get_json()
         



def register():
    plugin = Plugin()
    plugin_manager.subscribe_hook('get_comments', 'ipfs', plugin.get_comments)
    plugin_manager.subscribe_hook('add_comment', 'ipfs', plugin.add_comment)
