#!/bin/bash

PYTHONPATH=${PYTHONPATH}:../shutit-scripts/minishift

python oc-priv-access.py
