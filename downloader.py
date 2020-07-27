# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
import mimetypes
from iiif_prezi.loader import ManifestReader
from urllib import request


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
    with request.urlopen(args.url) as response:
        assert response.getcode() == 200
        data = response.read()
    reader = ManifestReader(data)
    manifest = reader.read()

    # Get the sequence
    assert len(manifest.sequences) > 0
    sequence = manifest.sequences[0]
    canvases = sequence.canvases

    print("Downloading {} images of manifest \"{}\" to {}.".format(
        len(canvases),
        manifest.label,
        args.path
    ))

    for canvas in canvases:
        label = canvas.label
        print("Downloading {}...".format(label))
        annot = canvas.images[0]
        extension = mimetypes.guess_extension(annot.resource.format)
        request.urlretrieve(
            annot.resource.id,
            os.path.join(args.path, label + extension)
        )
