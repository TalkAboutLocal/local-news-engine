import json
import collections

"""

python camdennewjournal_summary.py | sort -nr | head -n 1000 | gist-paste -p -u d8000e1aa0acccd3cf4665bb0fcc221c
outputs top 1000 entities with more than one word to a gist:
https://gist.github.com/Bjwebb/d8000e1aa0acccd3cf4665bb0fcc221c

"""

with open('data/saved_camdennewjournal_entities.json') as fp:
    entities = json.load(fp, object_pairs_hook=collections.OrderedDict)

for entity, pages in entities.items():
    # Only include entities with a space in
    # I think this is true of all names that we're realistically going to match
    if ' ' in entity:
        print(len(pages), entity)
    #    print(entity)
