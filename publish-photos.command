#!/bin/bash
# Double-click this file to publish the photo folders waiting in inbox/.
cd "$(dirname "$0")" || exit 1
python3 publish_photos.py
echo
read -n 1 -s -r -p "Press any key to close this window."
