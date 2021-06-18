pip install -r requirements.txt
rmdir /S /Q tmp
rmdir /S /Q dist
mkdir dist
mkdir tmp
mkdir tmp\capture
mkdir tmp\report
mkdir tmp\snapper_rds
pyinstaller --workpath tmp\build_capture --hidden-import=pg8000 --hidden-import=fsspec --hidden-import=s3fs --hidden-import=fsspec --distpath dist --specpath tmp\capture --paths statsanalyzer --onefile statsanalyzer\capture.py
pyinstaller --workpath tmp\build_report --hidden-import=fsspec --hidden-import=s3fs --distpath dist --specpath tmp\report --paths statsanalyzer --onefile statsanalyzer\report.py
pyinstaller --workpath tmp/build_snapper_rds --hidden-import=pg8000 --hidden-import=fsspec --hidden-import=s3fs --hidden-import=fsspec --distpath dist --specpath tmp\snapper_rds --paths statsanalyzer --onefile statsanalyzer\snapper_rds.py
rmdir /S /Q tmp