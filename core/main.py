#!/usr/bin/env python3

from core import app
from core import api

# only for development purposes
def run():
    app.run(debug=True, host='0.0.0.0')



