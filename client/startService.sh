#!/bin/sh
( ( nohup python3 runScript.py 1>logging.log 2>&1 ) & )