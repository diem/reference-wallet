# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import sys

from pubsub import DEFL_CONFIG, VASP_ADDR
from pubsub_proxy.proxy import LibraPubSubProxy
from pubsub_proxy.settings import Settings

parser = argparse.ArgumentParser(
    description="Pubsub CLI tool. Takes in pubsub config file or VASP_ADDR environment variable"
)
parser.add_argument("-f", "--file", type=str, help="LRW pubsub config file path")
args = parser.parse_args()

if args.file:
    try:
        with open(args.file) as f:
            conf = json.load(f)
    except:
        print("Missing or invalid config file, exiting...")
        sys.exit(1)
else:  # load in by env var
    if not VASP_ADDR:
        print("Missing VASP_ADDR environment variable, exiting...")
        sys.exit(1)
    conf = DEFL_CONFIG

print(conf)

settings = Settings(conf)
pubsub_client = LibraPubSubProxy(settings)

pubsub_client.start()
