#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import argparse
import subprocess
from urllib.parse import urlparse
from requests.exceptions import ConnectionError

from core.tests import active_tests
from core.utils import host, format_result, extractHeaders
from core.colors import bad, end, red, run, good, grey, green, white, yellow

print('''
    %sＣＯＲＳ ＧＵＡＲＤＩＡＮ  %s{%sv1.0-beta%s}%s
''' % (green, white, grey, white, end))

try:
    import concurrent.futures
except ImportError:
    print(' %s CorsGuardian needs Python > 3.4 to run.' % bad)
    quit()

parser = argparse.ArgumentParser()
parser.add_argument('-u', help='target url', dest='target')
parser.add_argument('-o', help='json output file', dest='json_file')
parser.add_argument('-d', help='request delay', dest='delay', type=float, default=0)
parser.add_argument('-q', help='don\'t print help tips', dest='quiet', action='store_true')
parser.add_argument('--headers', help='add headers', dest='header_dict', nargs='?', const=True)
args = parser.parse_args()

delay = args.delay
quiet = args.quiet
target = args.target
json_file = args.json_file
header_dict = args.header_dict

if type(header_dict) == bool:
    header_dict = extractHeaders(input("Enter headers (comma-separated key:value pairs): "))
elif type(header_dict) == str:
    header_dict = extractHeaders(header_dict)
else:
    header_dict = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip',
        'DNT': '1',
        'Connection': 'close',
    }

# Function to run DirBuster and extract valid URLs
def run_dirbuster(target):
    try:
        output = subprocess.check_output(['dirbuster', '-u', target, '-l', 'medium'])
        urls = output.decode('utf-8').split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        return urls
    except subprocess.CalledProcessError:
        print("Error running DirBuster.")
        return []

# Function to perform CORS scan on a URL
def cors(url):
    root = host(url)
    try:
        return active_tests(url, root, header_dict, delay)
    except ConnectionError as exc:
        print('%s Unable to connect to %s' % (bad, root))

if target:
    urls = run_dirbuster(target)
    if urls:
        print(f"Found {len(urls)} valid URLs.")
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(cors, url) for url in urls]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                if result:
                    print(good, result)
    else:
        print('No valid URLs found.')
else:
    print('No target URL specified.')
