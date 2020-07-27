# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import json
import os
import mimetypes
from iiif_prezi.loader import ManifestReader
from io import BytesIO
from PIL import Image
from urllib import request


def paste_tile(image, baseurl, x, y, w, h, ext='.jpg'):
    with request.urlopen(
        baseurl +
        '/{},{},{},{}'.format(x, y, w, h) +
        '/{},'.format(w) +
        '/0/default' + ext
    ) as response:
        assert response.getcode() == 200
        bytes_data = response.read()

    with BytesIO(bytes_data) as tmp:
        tile_image = Image.open(tmp)
        image.paste(tile_image, (x, y))


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
        with request.urlopen(annot.resource.service.id) as response:
            assert response.getcode() == 200
            image_info = json.loads(response.read())
        if 'tiles' in image_info:
            resource = annot.resource
            result = Image.new('RGB', (resource.width, resource.height))
            tile = image_info['tiles'][0]
            columns = resource.width // tile['width']
            rows = resource.height // tile['height']

            for row in range(rows):
                for column in range(columns):
                    paste_tile(
                        result,
                        annot.resource.service.id,
                        column * tile['width'],
                        row * tile['height'],
                        tile['width'],
                        tile['height'],
                        extension
                    )

                # Handle any leftover edge
                if resource.width % tile['width'] > 0:
                    paste_tile(
                        result,
                        annot.resource.service.id,
                        columns * tile['width'],
                        row * tile['height'],
                        resource.width % tile['width'],
                        tile['height'],
                        extension
                    )

            # Handle leftover edge at the bottom
            if resource.height % tile['height'] > 0:
                for column in range(columns):
                    paste_tile(
                        result,
                        annot.resource.service.id,
                        column * tile['width'],
                        rows * tile['height'],
                        tile['width'],
                        resource.height % tile['height'],
                        extension
                    )

                # Handle any leftover edge
                if resource.width % tile['width'] > 0:
                    paste_tile(
                        result,
                        annot.resource.service.id,
                        columns * tile['width'],
                        rows * tile['height'],
                        resource.width % tile['width'],
                        resource.height % tile['height'],
                        extension
                    )
            result.save(os.path.join(args.path, label + extension))
        else:
            request.urlretrieve(
                annot.resource.id,
                os.path.join(args.path, label + extension)
            )
