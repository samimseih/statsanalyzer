PYTHON3=$(which python3)
$PYTHON3 -m venv /tmp/build_statsanalyzer.$$
. /tmp/build_statsanalyzer.$$/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

pyinstaller build.spec

rm -rfv build

zip -r dist.zip dist

rm -rfv /tmp/build_statsanalyzer.$$
