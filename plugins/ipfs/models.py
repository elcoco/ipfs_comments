#!/usr/bin/env python3

import sys
from pprint import pprint
import inspect
import io
import json
from dataclasses import dataclass, field
from typing import Dict, List
import random

import ipfshttpclient


class NodeBaseClass():
    def __init__(self, client:ipfshttpclient, name:str=None):
        self._client = client
        self._name = name
        self._cid = None
        self._json = {"Name" : self._name}

    @property
    def json(self):
        return self._json

    @property
    def cid(self):
        return self._cid

    @property
    def name(self):
        return self._name

    def print(self, data=None, indent=0, prefix=''):
        magenta = "\033[35m"
        white = "\033[37m"
        green = "\033[32m"
        reset = "\033[0m"

        if data == None:
            data = self._client.dag.get(self._cid).as_json()

        spaces = " " * indent

        if type(data) == list:
            print(spaces + prefix + green + f"ARRAY[{len(data)}]" + reset)
            for i,item in enumerate(data):
                self.print(item, prefix=f"[{i}] ", indent=indent+2)

        elif type(data) == dict:
            print(spaces + magenta + prefix + "DICT" + reset)
            for k,v in data.items():
                if k == '/':
                    d = self._client.dag.get(v).as_json()
                    self.print(d, prefix=f"{white}{k}:{reset} ", indent=indent+2)
                else:
                    if v == None:
                        continue
                    self.print(v, prefix=f"{white}{k}:{reset} ", indent=indent+2)
        else:
            print(spaces + prefix + "\t" + str(data))

    def add_link(self, key, node):
        """ Append a link in the list at key """
        if not key in self._json.keys():
            self._json[key] = []

        link = {node.name: {'/' : node.cid}}
        self._json[key].append(link)

    def write(self):
        res = self._client.dag.put(io.BytesIO(json.dumps(self._json).encode()))
        self._cid = res['Cid']['/']
        return self._cid


class RootNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json["Sites"] = []


class SiteNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json["Blogs"] = []
        self._json["Pages"] = []


class BlogNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json["Posts"] = []

class PostNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json["Comments"] = []


class CommentNode(NodeBaseClass):
    def __init__(self, author, date_time, reply_to, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._json["Author"] = author
        self._json["DateTime"] = date_time
        self._json["ReplyTo"] = reply_to
        self._json["Content"] = content


def write_node():
    with ipfshttpclient.connect() as client:

        root = RootNode(client, 'disko')
        for i in range(2):
            site = SiteNode(client, f"site_{i}")

            for i in range(1):
                blog = BlogNode(client, f"blog_{i}")

                for i in range(3):
                    post = PostNode(client, f"post_{i}")

                    for i in range(3):
                        comment = CommentNode("bever",
                                              "2021-02-33 23:34",
                                              None,
                                              "post content",
                                              client,
                                              f"comment_title_{i}")
                        comment.write()
                        post.add_link("Comments", comment)

                    post.write()
                    blog.add_link("Posts", post)

                blog.write()
                site.add_link("Blogs", blog)

            site.write()
            root.add_link("Sites", site)

        root.write()
        root.print()
        print(root.cid)
        return root.cid
