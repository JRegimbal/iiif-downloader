# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import concurrent.futures as futures
import json
import os
import mimetypes
from iiif_prezi.loader import ManifestReader
from io import BytesIO
from PIL import Image
from urllib import request


def unique_filename(name, extension):
    if not os.path.exists(name + extension):
        return name + extension
    num = 1
    while os.path.exists(name + ' - ' + str(num) + extension):
        num += 1
    return name + ' - ' + str(num) + extension


def get_tile(baseurl, x, y, w, h, ext='.jpg'):
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
        tile_image.load()
    return (tile_image, (x, y))


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
            raw_data = response.read()
            content_type = response.getheader('Content-Type')
        if content_type == 'application/json' or \
                content_type == 'application/ld+json':
            image_info = json.loads(response.read())
            if 'tiles' in image_info:
                resource = annot.resource
                result = Image.new('RGB', (resource.width, resource.height))
                tile = image_info['tiles'][0]
                columns = resource.width // tile['width']
                rows = resource.height // tile['height']

                futures_results = []
                with futures.ThreadPoolExecutor(max_workers=10) as executor:
                    for row in range(rows):
                        for column in range(columns):
                            futures_results.append(executor.submit(
                                get_tile,
                                annot.resource.service.id,
                                column * tile['width'],
                                row * tile['height'],
                                tile['width'],
                                tile['height'],
                                extension
                            ))

                        # Handle any leftover edge
                        if resource.width % tile['width'] > 0:
                            futures_results.append(executor.submit(
                                get_tile,
                                annot.resource.service.id,
                                columns * tile['width'],
                                row * tile['height'],
                                resource.width % tile['width'],
                                tile['height'],
                                extension
                            ))

                    # Handle leftover edge at the bottom
                    if resource.height % tile['height'] > 0:
                        for column in range(columns):
                            futures_results.append(executor.submit(
                                get_tile,
                                annot.resource.service.id,
                                column * tile['width'],
                                rows * tile['height'],
                                tile['width'],
                                resource.height % tile['height'],
                                extension
                            ))

                        # Handle any leftover edge
                        if resource.width % tile['width'] > 0:
                            futures_results.append(executor.submit(
                                get_tile,
                                annot.resource.service.id,
                                columns * tile['width'],
                                rows * tile['height'],
                                resource.width % tile['width'],
                                resource.height % tile['height'],
                                extension
                            ))
                    for future in futures.as_completed(futures_results):
                        tile_img, coord = future.result()
                        result.paste(tile_img, coord)
                    filename = unique_filename(
                        os.path.join(args.path, label),
                        extension
                    )
                    result.save(filename)
        else:
            filename = unique_filename(
                os.path.join(args.path, label),
                extension
            )
            request.urlretrieve(
                annot.resource.id,
                filename
            )
