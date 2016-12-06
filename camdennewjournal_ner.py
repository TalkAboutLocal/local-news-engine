import os
import re
import glob
import nltk
import json
import calendar
import argparse
import datetime
import dateutil.parser
import lxml.html as html
from collections import defaultdict

"""

Some setup is required to run this script:

Mirror the site with wget (warning this will take hours):
```
# Remove any files that already exist
rm -r data/www.camdennewjournal.com
time wget -m "http://www.camdennewjournal.com/" -X sites -P data --restrict-file-names=nocontrol --adjust-extension --accept-regex='^http://www.camdennewjournal.com/[^/]*[^\?]*$' 2> data/wget.log
```

-X sites
    Exclude anythign under /sites/ - this avoids downloading images/CSS/JS
-P data
    Place the downloaded files in the data/ directory
--restrict-file-names=nocontrol
    We need this for wget to save UTF-8 filenames properly
--adjust-extension
    Add a file extension so that file and directory names don't clash
    https://github.com/TalkAboutLocal/local-news-engine/issues/68
--accept-regex
    This has a regex to allow http://www.camdennewjournal.com/news?page=1 but not http://www.camdennewjournal.com/news/thisshouldreally404?page=1


Then run ``python camdennewjournal_ner.py``. 



Running for islingtontribune.com:
```
# Remove any files that already exist
rm -r data/www.islingtontribune.com
time wget -m "http://www.islingtontribune.com/" -X sites -P data --restrict-file-names=nocontrol --adjust-extension --accept-regex='^http://www.islingtontribune.com/[^/]*[^\?]*$' 2> data/wget_islingtontribune.log
```

Then run ``python camdennewjournal_ner.py --inputdir ./data/www.islingtontribune.com --output data/saved_islingtontribune_entities.json``.


"""

def json_set_default(obj):
    """
    We pass this function to the `default` keyword argument of json.dump to
    ensure sets can be serialized.

    """
    if isinstance(obj, set):
        return list(obj)


def extract_entity_names(tree):
    if hasattr(tree, 'label'):
        if tree.label() == 'NE':
            yield ' '.join([child[0] for child in tree])
        else:
            for child in tree:
                yield from extract_entity_names(child)

def extract_entity_names_from_text(text):
    sentences = nltk.sent_tokenize(text)
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=True)
    for tree in chunked_sentences:
        return set(extract_entity_names(tree))


def write_json(entity_names):
    with open(args.output, 'w') as fp:
        json.dump(entity_names, fp, default=json_set_default, indent=4, sort_keys=True)


# Parse commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument('--inputdir', default='./data/www.camdennewjournal.com')
parser.add_argument('--output', default='data/saved_camdennewjournal_entities.json')
args = parser.parse_args()



# Download required nltk data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')



entity_names = defaultdict(list)
i = 0


for fname in glob.glob(args.inputdir+'/**', recursive=True):
    if os.path.isdir(fname):
        continue
    try:
        doc = html.parse(fname)
    except UnicodeEncodeError:
        print('Bad filename '+repr(fname))
        continue
    content = doc.find('//div[@class="node"]/div[@class="content"]')
    if content is not None:
        text = content.text_content()

        date = None
        # Looks like Camden New journal manually adds these dates to the text
        # of the article. A text match seems to be the most reliable way to extract these.
        # Check for the word 'Published: ' followed by 3 more words.
        m = re.search('Published:\s+(\S+\s+\S+\s+\S+)', text)
        if m:
            date_text = m.group(1)
            try:
                date = dateutil.parser.parse(date_text, fuzzy=True)
            except (calendar.IllegalMonthError, ValueError):
                pass
        else:
            print('No date found on {}'.format(fname))

        # Ignore dates in the future
        if date and date.date() > datetime.date.today():
            date = None

        i += 1
        for name in extract_entity_names_from_text(text):
            entity_names[name].append({
                'link': fname.replace('.html', '').replace('./data/', 'http://'),
                '_recency': date.isoformat() if date else None
            })
        if i % 1000 == 0:
            print('writing intermediate json')
            write_json(entity_names)

print('writing final json')
write_json(entity_names)
