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
import hashlib
import datetime

from core.exceptions import BadRequestError, NotFoundError
from core import config

import ipfshttpclient

logger = logging.getLogger('app')

class NodeBaseClass():
    def __init__(self, client:ipfshttpclient):
        self._client = client
        self.cid = None

    def write(self):
        res = self._client.dag.put(io.BytesIO(json.dumps(self.get_json()).encode()))
        self.cid = res['Cid']['/']
        return self.cid

    def get_dag(self, cid):
        """ Get dag object from IPFS """
        return self._client.dag.get(cid).as_json()


class Comment(NodeBaseClass):
    def __init__(self, client:ipfshttpclient, page_id=None, author=None, reply_to=None, content=None):
        super().__init__(client)

        #self.datetime = datetime.datetime.utcnow().timestamp()
        self.datetime = str(datetime.datetime.utcnow())
        self.page_id = page_id
        self.author = author
        self.content = content
        self.reply_to = reply_to
        self.id = str(hashlib.sha256((str(self.datetime) + str(self.author) + str(self.content)).encode()).hexdigest())
        self._client = client

    def get_json(self):
        return { "author"  :  self.author,
                 "dateTime" : self.datetime,
                 "content" :  self.content,
                 "cid" :      self.cid,
                 "replyTo" :  self.reply_to,
                 "id":        self.id }

    def read_from_cid(self, cid):
        dag = self.get_dag(cid)
        self.author = dag["author"]
        self.content = dag["content"]
        self.datetime = dag["dateTime"]
        self.id = dag["id"]
        self.reply_to = dag["replyTo"]
        self.cid = cid


class Root(NodeBaseClass):
    def __init__(self, client:ipfshttpclient):
        super().__init__(client)
        self._json = {"sites" : {}}
        self._comments = []

    def add_comment(self, comment):
        self._comments.append(comment)

    def get_comments(self, page_id):
        comments = [x.get_json() for x in self._comments if x.page_id == page_id]
        comments.sort(key=lambda x: datetime.datetime.strptime(x["dateTime"], "%Y-%m-%d %H:%M:%S.%f"), reverse=True)
        return comments

    def get_json(self):
        json = {"pages" : {}}

        for c in self._comments:
            if c.page_id not in json["pages"].keys():
                json["pages"][c.page_id] = {}

            json["pages"][c.page_id][c.id] = {'/' : c.cid}

        return json

    def read_from_cid(self, cid):
        dag = self.get_dag(cid)

        for page_id, comments in dag["pages"].items():
            for _, k in comments.items():
                c = Comment(self._client, page_id=page_id)
                c.read_from_cid(k['/'])
                self._comments.append(c)
