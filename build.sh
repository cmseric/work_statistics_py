#!/bin/bash
timestamp=$(date +"%Y%m%d_%H%M%S")
pyinstaller -F -w -n "WorkTracker_$timestamp" your_script.py
