#!/usr/bin/bash
pipenv uninstall northstar && pipenv install -e git+https://github.com/northstaratlas/northstar.git#egg=northstar
