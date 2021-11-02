import datetime

from flask import jsonify


def message(msg='', data={}):
    d = {}
    d["message"] = msg
    d["status_code"] = 200
    d["payload"] = data
    d["time"] = datetime.datetime.utcnow()
    return jsonify(d)
