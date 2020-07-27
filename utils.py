# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

from urllib import request
import json


def fetch(url):
    with request.urlopen(url) as response:
        assert response.getcode() == 200
        return json.loads(response.read())


def get_manifest(url):
    manifest = fetch(url)
    assert manifest["@type"] == "sc:Manifest"
    return manifest



