# Copyright © 2020 Juliette Regimbal
# SPDX-License-Identifier: GPL-3.0-or-later

from concurrent import futures
import json
import os
import mimetypes
from iiif_prezi.loader import ManifestReader
from io import BytesIO
from PIL import Image
from urllib import request


THREADS_NUM = 6


def unique_filename(name, extension):
    """Generate unique filename by adding number"""
    if not os.path.exists(name + extension):
        return name + extension
    num = 1
    while os.path.exists("{} ({}){}".format(name, str(num), extension)):
        num += 1
    return "{} ({}){}".format(name, str(num), extension)


def get_tile(baseurl, x, y, w, h, ext='.jpg'):
    """Download tile with specified bounds at full res."""
    url = "{0}/{1},{2},{3},{4}/{3},/0/default{5}".format(
        baseurl,
        x,
        y,
        w,
        h,
        ext
    )

    with request.urlopen(url) as response:
        assert response.getcode() == 200
        bytes_data = response.read()

    with BytesIO(bytes_data) as fp:
        tile_image = Image.open(fp)
        tile_image.load()
    return (tile_image, (x, y))


def get_image(canvas):
    """Get Image data from canvas"""
    resource = canvas.images[0].resource
    with request.urlopen(resource.service.id + '/info.json') as response:
        assert response.getcode() == 200
        raw_data = response.read()
    return json.loads(raw_data)


def download_canvas(canvas, path, prefix=""):
    """Download canvas at a URL to a path"""
    label = canvas.label
    basename = os.path.join(path, prefix + label)
    resource = canvas.images[0].resource
    ext = mimetypes.guess_extension(resource.format)

    # Try to get full image at once.
    with request.urlopen(resource.id) as response:
        assert response.getcode() == 200
        raw_data = response.read()
    with BytesIO(raw_data) as fp:
        full_img = Image.open(fp)
        full_img.load()

    if full_img.width != canvas.width:
        # Oops we need to use tiles...
        image = get_image(canvas)
        full_img = Image.new('RGB', (resource.width, resource.height))
        tile = image['tiles'][0]
        columns = resource.width // tile['width']
        rows = resource.height // tile['height']
        results = []

        # Using threads to download multiple tiles at once
        with futures.ThreadPoolExecutor(max_workers=THREADS_NUM) as executor:
            for row in range(rows):
                for column in range(columns):
                    results.append(executor.submit(
                        get_tile,
                        resource.service.id,
                        column * tile['width'],
                        row * tile['height'],
                        tile['width'],
                        tile['height'],
                        ext
                    ))

                # Handle horizontal leftover edge
                if resource.width % tile['width'] > 0:
                    results.append(executor.submit(
                        get_tile,
                        resource.service.id,
                        columns * tile['width'],
                        row * tile['height'],
                        resource.width % tile['width'],
                        tile['height'],
                        ext
                    ))

            # Leftover edge at bottom
            if resource.height % tile['height'] > 0:
                for column in range(columns):
                    results.append(executor.submit(
                        get_tile,
                        resource.service.id,
                        column * tile['width'],
                        rows * tile['height'],
                        tile['width'],
                        resource.height % tile['height'],
                        ext
                    ))

                if resource.width % tile['width'] > 0:
                    results.append(executor.submit(
                        get_tile,
                        resource.service.id,
                        columns * tile['width'],
                        rows * tile['height'],
                        resource.width % tile['width'],
                        resource.height % tile['height'],
                        ext
                    ))
            # Paste tiles together as they finish...
            for future in futures.as_completed(results):
                try:
                    tile_img, coord = future.result()
                    full_img.paste(tile_img, coord)
                except Exception as e:
                    print(e)
                    print("Skipping this tile!")

    # Save image
    filename = unique_filename(basename, ext)
    full_img.save(filename)


def get_manifest(url):
    """Download the manifest from url"""
    try:
        with request.urlopen(url) as response:
            reader = ManifestReader(response.read())
        return reader.read()
    except Exception:
        return None


def process_manifest(url, path, include_label=False):
    """Process and download manifest by url"""
    # Download manifest
    with request.urlopen(url) as response:
        assert response.getcode() == 200
        reader = ManifestReader(response.read)
    manifest = reader.read()

    # Should we go through every sequence or only the first?
    assert len(manifest.sequences) > 0
    sequence = manifest.sequences[0]
    canvases = sequence.canvases

    prefix = manifest.label if include_label else ""

    for canvas in canvases:
        download_canvas(canvas, path, prefix)
