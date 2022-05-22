#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Flower.
#
# Copyright ©2018 Nicolò Mazzucato
# Copyright ©2018 Antonio Groza
# Copyright ©2018 Brunello Simone
# Copyright ©2018 Alessio Marotta
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# 
# Flower is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Flower is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flower.  If not, see <https://www.gnu.org/licenses/>.

from http.server import BaseHTTPRequestHandler
from io import BytesIO
import json

#class to parse request informations
class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, raw_http_request):
        self.rfile = BytesIO(raw_http_request)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

        self.headers = dict(self.headers)
        # Data
        try:
            self.data = raw_http_request[raw_http_request.index(
                b'\n\n')+2:].rstrip()
        except ValueError:
            self.data = None

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

# tokenize used for automatically fill data param of request
def convert_http_requests(raw_request, tokenize=True, use_requests_session=False):
    request = HTTPRequest(raw_request)
    body = raw_request.split(b"\r\n\r\n", 1)

    data = {}
    headers = {}

    blocked_headers = ["content-length", "accept-encoding", "connection", "accept", "host"]
    content_type = ""
    data_param_name = "data"

    for i in request.headers:
        normalized_header = i.lower()

        if normalized_header == "content-type":
            content_type = request.headers[i]
        if not normalized_header in blocked_headers:
            headers[i] = request.headers[i]

    # if tokenization is enabled and body is not empty, try to decode form body or JSON body
    if tokenize and len(body) > 1 and body[1].strip():
        # try to deserialize form data
        if content_type.startswith("application/x-www-form-urlencoded"):
            data_param_name = "data"
            for i in body[1].decode().split("&"):
                d = i.split("=")
                data[d[0]] = d[1]

        # try to deserialize json
        if content_type.startswith("application/json"):
            data_param_name = "json"
            data = json.loads(body[1])

        # try to use raw text
        if content_type.startswith("text/plain"):
            data_param_name = "data"
            data = body[1]

        # try to extract files
        if content_type.startswith("multipart/form-data"):
            data_param_name = "files"
            return "Forms with files are not yet implemented"

    # Check if we want to use Python requests.Session()
    if use_requests_session:
        return """import os
import requests

host = os.getenv("TARGET_IP")

s = requests.Session()

s.headers = {}

data = {}

s.{}("http://{{}}{}".format(host), {}=data, headers=headers)""".format(
        str(dict(headers)),
        data,
        request.command.lower(),
        request.path,
        data_param_name,
    )

    else:
        return """import os
import requests

host = os.getenv("TARGET_IP")

headers = {}

data = {}

requests.{}("http://{{}}{}".format(host), {}=data, headers=headers)""".format(
        str(dict(headers)),
        data,
        request.command.lower(),
        request.path,
        data_param_name,
    )
