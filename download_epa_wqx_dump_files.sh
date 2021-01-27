#!/bin/bash
# download the Postgres wqx dump files from the epa
# looks for the epa download python script in the same directory as this script
# usage: download_epq_wqx_dump_files.sh [script options]
script_dir=`dirname $0`
script="$script_dir/epa_wqx_download.py"

echo Installing python requirements
pip3 install -r $script_dir/requirements.txt

echo Running epa download: $script $*
python $script $*
