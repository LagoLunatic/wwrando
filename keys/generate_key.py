#!/usr/bin/python3.10

import secrets
import sys

num_bytes = int(sys.argv[1]) if len(sys.argv) > 1 else 16
print(secrets.token_hex(num_bytes))
