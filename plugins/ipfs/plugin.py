#!/usr/bin/env python3

from core.exceptions import NotFoundError
import logging
from pathlib import Path
from pprint import pprint
import datetime
from typing import Dict, List

from core import plugin_manager
from core import config
from core.exceptions import BadRequestError


from plugins.ipfs.models import Root, Comment

import ipfshttpclient

logger = logging.getLogger('app')


class Plugin():
    def __init__(self):
        self.name = 'ipfs'

        # write brand new dag if it doesn't exist yet
        if not config['plugins']["ipfs"]["root_cid"]:
            with ipfshttpclient.connect() as client:
                print("No CID found in config file, generating new DAG")
                root = Root(client)
                root.write()
                config['plugins']["ipfs"]["root_cid"] = root.cid
                config.write()
                print(f"Created new dag: {root.cid}")

    def get_comments(self, page_id: str) -> List[Dict]:
        with ipfshttpclient.connect() as client:
            root = Root(client)
            root.read_from_cid(config['plugins']["ipfs"]["root_cid"])

        return root.get_comments(page_id)

    def ipns_publish(self, cid: str, key: str=None):
        logger.debug("Starting publish to IPNS")
        with ipfshttpclient.connect() as client:
            response = client.name.publish(cid, key=key)
        logger.debug(f"Published CID to {response['Name']}")

    def add_comment(self, page_id: str, data: Dict) -> Dict:
        with ipfshttpclient.connect() as client:
            root = Root(client)
            root.read_from_cid(config['plugins']["ipfs"]["root_cid"])

            comment = Comment(client,
                              page_id = page_id,
                              author = data["author"],
                              reply_to = data["replyTo"],
                              content = data["content"])
            comment.write()

            root.add_comment(comment)
            cid = root.write()

        # save and write changed root_cid to disk
        config['plugins']['ipfs']['root_cid'] = cid
        config.write()

        #self.ipns_publish(cid)
                              
        logger.debug(">>>> Root CID: "+ cid)
        return comment.get_json()


def register():
    plugin = Plugin()
    plugin_manager.subscribe_hook('get_comments', 'ipfs', plugin.get_comments)
    plugin_manager.subscribe_hook('add_comment', 'ipfs', plugin.add_comment)
