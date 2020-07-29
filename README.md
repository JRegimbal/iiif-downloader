A tool to download a set of images from a IIIF presentation manifest using the IIIF image api for use with tools that do not support IIIF.

# Setup and Usage

This requires Python 3.x and the dependencies under `requirements.txt`.
These can be installed by running `pip install -r requirements.txt`.
From there, the tool an be called from the source directory by
```
python downloader.py
```

# Building

This uses wxPython and can (presumably) be built on any system it supports.
It has been tested on Linux (Debian bullseye) and macOS (High Sierra).

On Linux:
```
python -m PyInstaller --onefile --windowed --name iiif-downloader --add-data=env/lib/python3.8/site-packages/iiif_prezi/contexts/*.json:iiif_prezi/contexts downloader.py
```
On macOS:
```
python -m PyInstaller --windowed --name iiif-downloader --add-data=env/lib/python3.8/site-packages/iiif_prezi/contexts/*.json:iiif_prezi/contexts --hidden-import=pkg_resources.py2_warn downloader.py
```
