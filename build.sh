PYTHON3=$(which python3)
$PYTHON3 -m venv /tmp/build_statsanalyzer.$$
. /tmp/build_statsanalyzer.$$/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
rm -rfv dist
rm -rfv /tmp/capture
rm -rfv /tmp/report
rm -rfv /tmp/snapper_rds
rm -rfv /tmp/build_capture
rm -rfv /tmp/build_report
rm -rfv /tmp/build_snapper_rds
mkdir -p /tmp/capture
mkdir -p /tmp/report
mkdir -p /tmp/snapper_rds
pyinstaller \
	--workpath /tmp/build_capture \
	--hidden-import=pg8000 \
	--hidden-import=fsspec \
	--hidden-import=s3fs \
	--hidden-import=fsspec \
	--distpath dist/$1 \
	--specpath /tmp/capture \
	--paths statsanalyzer \
	--onefile statsanalyzer/capture.py
pyinstaller \
	--workpath /tmp/build_report \
	--hidden-import=fsspec \
	--hidden-import=s3fs \
	--distpath dist/$1 \
	--specpath /tmp/report \
	--paths statsanalyzer \
	--onefile statsanalyzer/report.py
pyinstaller \
    --workpath /tmp/build_snapper_rds \
	--hidden-import=pg8000 \
	--hidden-import=fsspec \
	--hidden-import=s3fs \
	--hidden-import=fsspec \
    --distpath dist/$1 \
    --specpath /tmp/snapper_rds \
    --paths statsanalyzer \
    --onefile statsanalyzer/snapper_rds.py
zip -r dist.zip dist
