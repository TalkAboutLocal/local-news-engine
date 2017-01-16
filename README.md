# Local News Engine

Local News Engine is prototype software by [Talk About Local](https://talkaboutlocal.org.uk/). You can find out more about the project on the [Talk About Local blog](https://talkaboutlocal.org.uk/local-news-engine-prototype/). Development has been funded by [Google Digital News Initiative](https://www.digitalnewsinitiative.com/). The software is being developed by [Open Data Services](http://opendataservices.coop).

LNE helps local and hyperlocal journalists and bloggers work with public data that, while often available to the public, is difficult to work with - especially for time-pressured journalists. 

At the prototype stage, LNE is a toolkit containing:
* Scrapers / downloaders for three public data sources - planning and licensing records for the London Boroughs of Camden and Islington
* A parser for magistrates courts lists
* Tools to create three HTML files:
  * **leads.html** - A list of names which appear in two or more sources, and which may therefore be a lead to a story
  * **explore.html** - An aggregate list of all records from all sources, with tools to filter by London wards

## Running Local News Engine

### Setup

You will need Python3 (with virtualenv), NPM and golang installed - e.g. on Ubuntu

```
sudo aptitude install python3-virtualenv npm golang
```

Install python requirements
```
python3 -m virtualenv --python=python3 .ve
source .ve/bin/activate
pip install -r requirements.txt
```

Install javascript requirements
```
npm install .
```

### Courts Data

Get a courts file put it in the data directory and use pdftotext on it with layout command.

```
pdftotext -layout courts_data/courts.pdf
```
Then run parse the data which creates courts.txt

```
python courts_parse.py
```

The courts data parser writes its output to the courts_data directory. 

### Licensing and planning data

The scrapers put their results in the data directory

```
python islington_license.py 
python islington_planning.py 
python camden_license.py 
```
In order to rerun these the files created must be removed or moved.

For Camden planning

```
cd data
wget https://opendata.camden.gov.uk/resource/mcgw-i4rx.json
cd ..
```

### Camden New Journal & Islington Tribune entity recognition

See the top of [camdennewjournal_ner.py](camdennewjournal_ner.py).


### Name matching

The data for leads.html is generated by grouping the names by fuzzy matching, such that each group represents a single person with a certain degree of confidence. This generally works well for typos and different forms of the same name, but can give false positives in case of similar names. The output of this should always be treated with caution! To do the matching, run:

```
python name_matches.py
```

This also runs the go matching webserver in the background and kills it once used. All processed data can be found in the processed directory.

### Area matching

To process the data to obtain area information, run:
 
```
python area_matches.py
```

All processed data can be found in the processed directory.

### Running without the courts data

Create a dummy courts data file:

```
echo '[]' > courts_data/courts.json 
```

## Generating the HTML

All HTML can be found in the output directory.

Firstly the frontend templates need to be compiled
```
node_modules/.bin/nunjucks-precompile templates_nunjucks > output/templates.js
```

Then to generate the final html

```
python generate_html.py
```

