import datetime

from flask import jsonify


def message(msg='ok', payload={}):
    d = {}
    d["message"] = msg
    d["status_code"] = 200
    d["payload"] = payload
    d["time"] = datetime.datetime.utcnow()

    response = jsonify(d)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
