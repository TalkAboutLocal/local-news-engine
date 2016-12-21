import csv
import json
import collections
from load_and_normalize_data import all_names
import subprocess
import requests
import time

data = "\n".join('"' + name + '"' for name in all_names)
encoded_data = data.encode("utf8")


proc = subprocess.Popen(["go", "run", "cluster.go"]) 

time.sleep(5)
with open('processed/matches.csv', 'w+') as matches:
    res = requests.post('http://127.0.0.1:9999/cluster', data=encoded_data)
    matches.write(res.text)
    proc.kill()


with open("processed/matches.csv") as matches:
    reader = csv.reader(matches)
    for row in reader:
        if row[1] != row[2]:
            match_list = all_names.pop(row[2])
            for item in match_list:
                item['fuzzy_match'] = row[2]
                all_names[row[1]].append(item)

interesting_names = []


for key, value in all_names.items():
    counted_sources = collections.Counter(item["source"] for item in value if item["source_type"] != "Name")
    counted_name_sources = collections.Counter(item["source"] for item in value if item["source_type"] == "Name")
    info = {
        "counted_source": dict(counted_sources),
        "counted_name_source": dict(counted_name_sources),
        "total_sources": len(value),
        "fuzzy_names": list(set(item['fuzzy_match'] for item in value if 'fuzzy_match' in item))
    }

    distinct_name_sources = set()
    distinct_data_sources = set()

    value.sort(key=lambda x: x.get('data', {}).get("_recency") or "", reverse=True)


    for item in value:
        if item["source_type"] == "Name" :
            distinct_name_sources.add(item['source_type'])
        else:
            distinct_data_sources.add(item['source_type'])
        recency = item

    if len(distinct_data_sources) > 1 or (distinct_name_sources and distinct_data_sources):
        interesting_names.append((value[0].get('data', {}).get("_recency",""), key, value, info))


interesting_names.sort(reverse=True)


with open("processed/interesting_names.json", "w+") as interesting_names_file:
    json.dump(interesting_names, interesting_names_file, indent=2)
