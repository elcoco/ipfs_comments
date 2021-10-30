#!/usr/bin/env python3

from pprint import pprint
import inspect
import io
import json
from dataclasses import dataclass, field
from typing import Dict, List

import ipfshttpclient

@dataclass
class BaseObject():
    client: ipfshttpclient

    data: str
    size: int = 8

    # name of file and link when added to other object
    name: str = None

    object_hash: str = field(default=None)


    def print(self, object_hash=None, spaces=0):
        """ Recursive print of dag object, get data from network not from objects """

        if object_hash == None:
            object_hash = self.object_hash

        space = spaces * ' '

        dag = self.client.dag.get(object_hash)

        print(space + "object:", object_hash)
        print(space + "    data:", dag["data"])

        for link in dag["links"]:
            if 'Cid' in link.keys():
                link_hash = link['Cid']['/']
            else:
                link_hash = link['Hash']

            # is dag object
            if link_hash.startswith('ba'):
                self.print(link_hash, spaces+4)

            # is dir
            elif link_hash.startswith('Qm') and self.client.dag.get(link_hash)['links']:
                self.print(link_hash, spaces+4)

            # is file
            elif link_hash.startswith('Qm'):
                print(space + "    name:", link["Name"])
                print(space + "        hash:   ", link_hash)
                print(space + "        size:   ", link["Size"])
                print(space + "        content:", self.client.cat(link_hash).decode())
            else:
                print("!!! Unknown data type !!!")


@dataclass
class FileObject(BaseObject):
    def write(self):
        f = io.BytesIO(self.data.encode())
        f.name = self.name
        res = client.add(f)
        self.size = int(res['Size'])
        self.object_hash = res['Hash']
        return res


@dataclass
class DagObject(BaseObject):
    """ Object can contain links to other objects or files """
    links: list = field(default_factory=list)

    def add_link(self, obj):
        self.links.append(obj)

    def write(self):
        obj = self.as_dict()
        ret = self.client.dag.put(io.BytesIO(json.dumps(obj).encode()))
        self.object_hash = ret['Cid']['/']
        return self.object_hash

    def as_dict(self):
        """ represent object as a dict so we can send it to ipfs client """
        d = {}
        d['data'] = self.data
        d['links'] = []
        for l in self.links:
            d['links'].append({ "Name" : l.name,
                                "Hash" : l.object_hash,
                                "Size" : l.size})
        return d


with ipfshttpclient.connect() as client:
    obj_1 = DagObject(client, 'object 1', name='obj1')
    obj_2 = DagObject(client, 'object 2', name='obj2')
    obj_3 = DagObject(client, 'object 3', name='obj3')
    obj_4 = DagObject(client, None, name="nested", object_hash="Qmeixng4edEFCn8YGWvkFNZXPZ9Fphuf6iHb4QaN9Fs3vA")

    obj_1.write()
    obj_2.write()
    obj_3.write()

    file_1 = FileObject(client, 'file contents disko!!!', name='file_1.txt')
    file_1.write()

    root_obj = DagObject(client, 'root object contents', name="root object")
    root_obj.add_link(obj_1)
    root_obj.add_link(obj_2)
    root_obj.add_link(obj_3)
    root_obj.add_link(obj_4)

    root_obj.add_link(file_1)

    root_obj.write()
    root_obj.print()
