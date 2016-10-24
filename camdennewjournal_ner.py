import os
import glob
import nltk
import json
import lxml.html as html
from collections import defaultdict

"""

Some setup is required to run this script:

Mirror the site with wget:
wget -m "http://www.camdennewjournal.com/" -X sites 

Download nltk data:
Open up a python prompt and:
import nltk
nltk.download()
d
punkt
d
averaged_perceptron_tagger
d
maxent_ne_chunker
d
words


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
        yield from extract_entity_names(tree)


def write_json(entity_names):
    with open('data/saved_camdennewjournal_entities.json', 'w') as fp:
        json.dump(entity_names, fp, default=json_set_default, indent=4, sort_keys=True)

entity_names = defaultdict(set)
i = 0


for fname in glob.glob('./www.camdennewjournal.com/**', recursive=True):
    if os.path.isdir(fname):
        continue
    try:
        doc = html.parse(fname)
    except UnicodeEncodeError:
        print('Bad filename '+repr(fname))
        continue
    content = doc.find('//div[@class="node"]/div[@class="content"]')
    if content is not None:
        i += 1
        text = content.text_content()
        for name in extract_entity_names_from_text(text):
            entity_names[name].add(fname)
        if i % 1000 == 0:
            print('writing intermediate json')
            write_json(entity_names)

print('writing final json')
write_json(entity_names)
