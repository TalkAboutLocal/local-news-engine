#!/bin/bash
set -e
python ../name_matches.py
python ../area_matches.py
../node_modules/.bin/nunjucks-precompile ../templates_nunjucks > output/templates.js
python ../generate_html.py
