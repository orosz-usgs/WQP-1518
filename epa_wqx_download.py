#!/usr/bin/python
from datetime import datetime
import os
import optparse
import re
import requests
from urllib.parse import urlparse

from multiprocessing import Pool, cpu_count
from functools import partial

# global constants
# root epa site containing wqx dump files to download
BASE_URL = 'https://www3.epa.gov/storet/download/storetw'

# Log file listing the wqx dump files to download
SUMMARY_LOG = 'wqx_dump_alltables_Weekly_pgsdp.log'

# directory where files are download to
DOWNLOAD_DIR = '.'

DATETIME_FORMAT = '%m/%d/%Y %H:%M:%S %Z'

def now():
    return datetime.now().astimezone().strftime(DATETIME_FORMAT)

# parse any commad line arguments provided
def parse_args():
    global DOWNLOAD_DIR
    parser = optparse.OptionParser()

    parser.add_option('-d', '--download-dir',
        action="store", dest="directory",
        help="Directory files are downloaded to", default=".")

    options, args = parser.parse_args()
    DOWNLOAD_DIR = options.directory

# cd to download directory if not current directory.
def cd_to_download_dir():
    if DOWNLOAD_DIR is not None and DOWNLOAD_DIR != '.':
        if not os.path.isdir(DOWNLOAD_DIR):
            raise Exception("Can not change directory to '{}' : directory not found.".format(DOWNLOAD_DIR))
        os.chdir(DOWNLOAD_DIR)

# Parse the summary log and construct urls to download the wqx dump files.
# returns list of urls
# format of lines with file names:
#-rw-r--r--. 1 postgres postgres 1676382936 Jan 11 02:56 wqx_dump_activity_Weekly_01_gz.aa
#-rw-r--r--. 1 postgres postgres 3294598572 Jan 11 02:57 wqx_dump_result_Weekly_02_gz.aa
def get_wqx_dump_file_urls():
    with open(SUMMARY_LOG) as log_file:
        contents = log_file.read()

    urls = []
    # parse out the lines with the file names
    pattern = re.compile(r'^-.*$', flags=re.MULTILINE)
    log_lines = pattern.findall(contents);
    for line in log_lines:
        fields = re.split(r'\s+', line)
        if len(fields) != 9:
            raise Exception('Error parsing summary log: expected 9 fields on line: ' + line)
        filename = fields[8]
        filename = os.path.basename(filename)
        if filename != SUMMARY_LOG:
            to_add = BASE_URL + '/' + filename
            if not to_add in urls:
                urls.append(to_add);

    # at a minuim, we expect dumps files for tables 'Result'
    return urls

# download the file specified by the url. If the file already exists locally, it is deleted.
def download_file(url, local_filename):
    # delete any previous download
    if os.path.exists(local_filename):
        os.remove(local_filename)
    # stream download
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(local_filename, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    else:
        print('ERROR http get {} returned {}'.format(url,str(r.status_code)))

# Download the summary log and save it locally.
def download_logs():
    url=BASE_URL + '/' + SUMMARY_LOG
    print('Downloading summary log: ' + url);
    download_file(url, SUMMARY_LOG)

# return the filename component of the specifed url
def get_filename(url):
    components = urlparse(url) # returns 6-item named tuple.
    filename = os.path.basename(components.path)
    return filename

# Download the file specifed by the url
def download_wqx_dump_file(url):
    filename = get_filename(url)
    print('   downloading --> {}'.format(url), flush=True)
    download_file(url, filename)
    return filename

def get_multi_part_downloads_dict(urls):
    files_dict = {}  # key is the filename of the combined file, value file parts
    # split .gz files hves _gz.a[a-z] ending
    pattern = re.compile(r'_gz\.[a-z][a-z]+$')
    for url in urls:
        filename = get_filename(url)
        if pattern.findall(filename):
            dest_file = re.sub(pattern, '.gz', filename)
            if dest_file in files_dict.keys():
                files_dict[dest_file].append(filename)
            else:
                file_list = [filename]
                files_dict[dest_file] = file_list

    # sort lists, so that files are combined in the expected order
    for key in files_dict.keys():
        files_dict[key].sort()

    return files_dict

def combine_files(dest_file, parts_list):
    print('   joining {} --> {}'.format(str(parts_list), dest_file), flush=True)
    read_size = 1024
    # Create a destination file to write to 
    with open(dest_file, 'wb') as output_file:
       # Go through each part one by one
       for file in parts_list:
           with open(file, 'rb') as input_file:
               while True:
                   # Read all bytes of the part
                   bytes = input_file.read(read_size)

                   # Break out of loop if we are at end of file
                   if not bytes:
                       break

                   # Write the bytes to the output file
                   output_file.write(bytes)

           # Close the input file
           input_file.close()

       # Close the output file
       output_file.close()

# add .dump file extension
def add_dump_extension(files_dict):
    for filename in files_dict.keys():
        if filename.endswith(".log"):
            continue

        new_name = ''
        if filename.endswith('.gz'):
            new_name = filename.replace('.gz', '.dump.gz')
        elif filename.endswith('_gz'):
            new_name = filename.replace('_gz', '.dump.gz')
        else: 
            new_name = filename + '.dump'

        print('   adding .dump extension: {} --> {}'.format(filename, new_name))
        os.rename(filename, new_name)

#
# Main
#
if __name__ == "__main__":
    print('EPA WQX Postgres dump download script started');
    print('System time is ' +  now());
    parse_args()
    cd_to_download_dir()
    print('Downloading files to: ' + os.getcwd())

    download_logs()
    urls=get_wqx_dump_file_urls();

    print("There are {} CPUs on this machine ".format(cpu_count()))
    print('Downloading epa WQX dump files and logs ({} in total)...'.format(len(urls)))
    with Pool(cpu_count()) as p:
        results = p.map(download_wqx_dump_file, urls)
        # Pool.close() is a little missed named. It does not shutdown the pool and
        # free up resources as File close() does. This prevents any more tasks from being
        # submitted to the pool. Needs to be called before using join() to wait for the
        # downloads (worker processes) to finish.
        p.close()
        p.join()

    print('File downloads completed at {}'.format(now()), flush=True)

    print('Combining multi part downloads...')
    files_dict = get_multi_part_downloads_dict(urls)
    for key in files_dict.keys():
        if len(files_dict[key]) == 1:
            # only one file, no combining needed. just rename
            print('   moving {} --> {}'.format(str(files_dict[key]), key))
            os.rename(files_dict[key][0], key)
        else: 
            combine_files(key, files_dict[key])

    # add .dump extension used by load script
    add_dump_extension(files_dict)

    print('EPA WQX Postgres dump downloads completed, time is ' +  now());
