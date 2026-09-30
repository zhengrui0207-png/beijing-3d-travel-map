#!/bin/zsh
cd -- "${0:A:h}"
python3 scripts/download_assets.py || exit 1
python3 server.py --open
