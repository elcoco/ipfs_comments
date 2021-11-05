#!/usr/bin/env python3

import sys
from pprint import pprint
import inspect
import io
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List
import random

import ipfshttpclient

logger = logging.getLogger('')

class NodeBaseClass():
    def __init__(self, client:ipfshttpclient, name:str=None, cid=None):
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

    def read_node(self, cid):
        """ Read full tree from cid, override this function """
        pass

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

        link = {node.name: {'/' : node.cid}, 'Name' : node.name}
        self._json[key].append(link)

    def write(self):
        res = self._client.dag.put(io.BytesIO(json.dumps(self.get_json()).encode()))
        self._cid = res['Cid']['/']
        return self._cid

    def get_dag(self, cid):
        return self._client.dag.get(cid).as_json()

    def node_factory(self, key, cid, _class):
        """ Create object from _class if key is found in ipfs data
            from cid """
        try:
            node_json = self.get_dag(cid)[key]
        except KeyError as e:
            print("Failed to find", e)
            return

        nodes = []
        for item in node_json:
            node = _class(self._client, item['Name'])
            node.read_node(item[item['Name']]['/'])
            nodes.append(node)

        return nodes


class RootNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sites = []

    def read_node(self, cid):
        """ Read object from ipld, retrieve children """
        self.sites = self.node_factory('Sites', cid, SiteNode)
        self._cid = cid

    def get_json(self):
        for s in self.sites:
            self.add_link("Sites", s)
        return self._json

    def get_comments(self, site_id, blog_id, post_id):
        try:
            site = next(iter([x for x in self.sites if x.name == site_id]))
            blog = next(iter([x for x in site.blogs if x.name == blog_id]))
            post = next(iter([x for x in blog.posts if x.name == post_id]))
            return post.comments
        except StopIteration as e:
            logger.error(f"Failed to find comments for: {site_id}>{blog_id}>{post_id}, error={e}")

    def write_tree(self):
        blogs = [b for sublist in self.sites for b in sublist.blogs]
        posts = [p for sublist in blogs for p in sublist.posts]
        comments = [c for sublist in posts for c in sublist.comments]

        for c in comments:
            c.write()
        for p in posts:
            p.write()
        for b in blogs:
            b.write()
        for s in self.sites:
            s.write()

        self.write()




class SiteNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blogs = []

    def read_node(self, cid):
        """ Read object from ipld, retrieve children """
        self.blogs = self.node_factory('Blogs', cid, BlogNode)
        self._cid = cid

    def get_json(self):
        for b in self.blogs:
            self.add_link("Blogs", b)
        return self._json


class BlogNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.posts = []

    def read_node(self, cid):
        """ Read object from ipld, retrieve children """
        self.posts = self.node_factory('Posts', cid, PostNode)
        self._cid = cid

    def get_json(self):
        for p in self.posts:
            self.add_link("Posts", p)
        return self._json


class PostNode(NodeBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.comments = []

    def read_node(self, cid):
        """ Read object from ipld, retrieve children """
        self.comments = self.node_factory('Comments', cid, CommentNode)
        self._cid = cid

    def get_json(self):
        for c in self.comments:
            self.add_link("Comments", c)
        return self._json


class CommentNode(NodeBaseClass):
    def __init__(self, *args, author=None, datetime=None, reply_to=None, content=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.datetime = datetime
        self.reply_to = reply_to
        self.content = content

    def read_node(self, cid):
        node_json = self.get_dag(cid)
        try:
            self.author = node_json['Author']
            self.datetime = node_json['DateTime']
            self.reply_to = node_json['ReplyTo']
            self.content = node_json['Content']
        except KeyError as e:
            print("Missing key:",e)
        self._cid = cid

    def get_json(self):
        self._json['Author'] = self.author
        self._json['Datetime'] = self.datetime
        self._json['ReplyTo'] = self.reply_to
        self._json['Content'] = self.content
        return self._json



def load_node(cid):
    with ipfshttpclient.connect() as client:
        root = RootNode(client, 'root')
        root.read_node(cid)
        return root



def write_node():
    with ipfshttpclient.connect() as client:

        root = RootNode(client, 'disko')
        for i in range(1):
            site = SiteNode(client, "chmod777")

            for i in range(1):
                blog = BlogNode(client, f"blog_{i}")

                for i in range(3):
                    post = PostNode(client, f"post_{i}")

                    for i in range(3):
                        comment = CommentNode(client,
                                              name=f"comment_title_{i}",
                                              author="bever",
                                              datetime="2021-02-33 23:34",
                                              reply_to=None,
                                              content="post content")
                        comment.write()
                        post.add_link("Comments", comment)

                    post.write()
                    blog.add_link("Posts", post)

                blog.write()
                site.add_link("Blogs", blog)

            site.write()
            root.add_link("Sites", site)

        root.write()
        #root.print()
        print(">>>>>>>>>>>>>>>>", root.cid)
        return root


def get_dag(cid):
    with ipfshttpclient.connect() as client:
        return client.dag.get(cid)



