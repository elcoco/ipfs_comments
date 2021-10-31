#!/usr/bin/env python3

import datetime
import sys
from pprint import pprint
import inspect
import io
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random

import ipfshttpclient


def get_rnd_string(length=5):
    return "".join([ str(chr(round(random.uniform(65,90)))) for i in range(length)])


@dataclass
class RootNode():
    client: ipfshttpclient
    blogs: List = field(default_factory=list)
    object_hash: Optional[str] = None

    def build_json(self):
        res = {}
        res['Blogs'] = []

        for blog in self.blogs:
            res['Blogs'].append(blog.get_json())
        return res

    def add_blog(self, blog):
        self.blogs.append(blog)
        
    def write_obj(self):
        res = self.client.dag.put(io.BytesIO(json.dumps(self.build_json()).encode()))
        self.object_hash = res['Cid']['/']
        return self.object_hash


@dataclass
class Blog():
    title: str
    posts: List = field(default_factory=list)

    def get_json(self):
        res = {}
        res['Title'] = self.title
        res['Posts'] = []
        for post in self.posts:
            res['Posts'].append(post.get_json())
        return res
    
    def add_post(self, post):
        self.posts.append(post)


@dataclass
class Post():
    title: str
    comments: List = field(default_factory=list)

    def get_json(self):
        res = {}
        res['Title'] = self.title
        res['Comments'] = []
        for comment in self.comments:
            res['Comments'].append(comment.get_json())
        return res

    def add_comment(self, comment):
        self.comments.append(comment)


@dataclass
class Comment():
    title: str
    datetime: str
    reply_to: Optional[str] #hash
    content: str

    def get_json(self):
        res = {}
        res['Title'] = self.title
        res['DateTime'] = self.datetime
        res['ReplyTo'] = self.reply_to
        res['Content'] = self.content
        return res

def fancy_print(data, prefix='', indent=0):
    magenta = "\033[35m"
    white = "\033[37m"
    green = "\033[32m"
    reset = "\033[0m"

    spaces = " " * indent
    if type(data) == list:
        print(spaces + prefix + green + "[" + reset)
        for i,item in enumerate(data):
            fancy_print(item, prefix=f"[{i}] ", indent=indent+4)
        print(spaces + green + "]" + reset)

    elif type(data) == dict:
        print(spaces + magenta + "{" + reset)
        for k,v in data.items():
            fancy_print(v, prefix=f"{white}{k}:{reset} ", indent=indent+4)
        print(spaces + magenta + "}" + reset)
    else:
        print(spaces + prefix + str(data))


def fancy_print(data, prefix='', indent=0):
    magenta = "\033[35m"
    white = "\033[37m"
    green = "\033[32m"
    reset = "\033[0m"

    spaces = " " * indent
    if type(data) == list:
        print(spaces + prefix + green + f"ARRAY[{len(data)}]" + reset)
        for i,item in enumerate(data):
            fancy_print(item, prefix=f"[{i}] ", indent=indent+4)

    elif type(data) == dict:
        print(spaces + magenta + prefix + "DICT" + reset)
        for k,v in data.items():
            fancy_print(v, prefix=f"{white}{k}:{reset} ", indent=indent+4)
    else:
        print(spaces + prefix + "\t" + str(data))

        
with ipfshttpclient.connect() as client:

    root = RootNode(client)
    for i in range(3):
        blog = Blog(f"blog_{i}")
        root.add_blog(blog)

        for i in range(3):
            post = Post(f"post_{i}")
            blog.add_post(post)

            for i in range(3):
                comment = Comment(f"super_title_{i}",
                                  "2021-02-33 23:34",
                                  None,
                                  "post content")
                post.add_comment(comment)

    root_hash = root.write_obj()

    fancy_print(client.dag.get(root_hash).as_json())
    print(root_hash)
    #fancy_print(root.build_json())






