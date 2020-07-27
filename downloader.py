# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
from utils import fetch


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download images from IIIF Presentation Manifest"
    )
    parser.add_argument("url", help="URL to manifest")
    parser.add_argument(
        "-p",
        "--path",
        help="location to download images",
        default="."
    )

    args = parser.parse_args()

    # Get the manifest
    manifest = fetch(args.url)
    assert manifest["@type"] == "sc:Manifest"

    # Get the sequence
    sequence = manifest["sequences"][0]
    assert sequence["@type"] == "sc:Sequence"
    canvases = sequence["canvases"]

    print("Downloading {} images of manifest \"{}\"... to {}".format(
        len(canvases),
        manifest["label"],
        args.path
    ))
