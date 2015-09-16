#!/usr/bin/env bash
rm -rf build dist furion.egg-info
python setup.py sdist
python setup.py bdist_wheel --universal
