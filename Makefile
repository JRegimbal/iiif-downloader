all:
	python -m PyInstaller --onefile --windowed --name iiif-downloader downloader.py

clean:
	$(RM) dist 
