#!/bin/bash

set -e

test -d data || echo "data dir not found"
test -d .git || echo "not the root of a git repo - you're probably in the wrong place"
which mail 1>/dev/null 2>/dev/null || echo "mail not found"
which gpg 1>/dev/null 2>/dev/null || echo "gpg not found"

# set up common functions
doMatch () {

version=$1

if [ $version = "courts" ] || [ $version = "noncourts" ]
then 

  echo "Preparing $version version..."

  echo "$version: Performing area matching..."
  python area_matches.py

  echo "$version: Performing name matching..."
  python name_matches.py

  echo "$version: Generating HTML..."
  python generate_html.py $version
  mv output/leads.html output/leads_${version}.html
  mv output/explore.html output/explore_${version}.html

  echo "$version: Zipping up..."
  zip local_news_engine$(date +"%d_%m_%y")_${version}.zip output/leads_${version}.html output/explore_${version}.html 
else 
  echo "Invalid version string specified"
  exit
fi

}

read -p "Before proceeding, ensure that you have run all scrapers, parsed the courts data and have a cup of coffee. Press [Enter] to continue:"

source bin/activate

echo "Compiling templates..."
node_modules/.bin/nunjucks-precompile templates_nunjucks > output/templates.js

for version in {courts,noncourts}; do
  doMatch $version
  echo '[]' > courts_data/courts.json 
done



message=<<EOF
Hi!

This is the latest delivery from the Local News Engine. Enjoy!

EOF

#echo $message $(uuencode local_news_engine$(date +"%d_%m_%y").zip local_news_engine$(date +"%d_%m_%y").zip) | mail rob.redpath@opendataservices.coop
