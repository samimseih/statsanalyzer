pip install -r requirements.txt
rm -rfv dist/$1
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
cd dist
mkdir $1
mv capture $1/.
mv snapper_rds $1/.
mv report $1/.
zip -r $1.zip $1
