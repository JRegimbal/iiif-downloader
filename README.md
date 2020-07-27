A tool to download a set of images from a IIIF presentation manifest using the IIIF image api for use with tools that do not support IIIF.

# Setup and Usage

This requires Python 3.x and the dependencies under `requirements.txt`.
These can be installed by running `pip install -r requirements.txt`.
From there, the tool an be called from the source directory by
```
python downloader.py [URL] -p [PATH_TO_DOWNLOAD_FILES]
```
