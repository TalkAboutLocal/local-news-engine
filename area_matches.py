import json

postcode_districts_of_interest = ["N1", "N7", "WC1", "NW1"]

area_of_interest = ["islington", "camden"]

from load_and_normalize_data import all_data

all_data.sort(key=lambda x: x.get("_recency", ""), reverse=True)

with open("processed/all_data.json", "w+") as all_data_file:
    json.dump(all_data, all_data_file, indent=2)


matches = []

for row in all_data:
    if row.get("_recency", "") < "2016":
        continue
    post_code_districts = row.get("_postcode_districts", [])
    for post_code_district in post_code_districts:
        if post_code_district in postcode_districts_of_interest:
            matches.append(row)
            continue

    all_string = " ".join(value for value in row.values() if isinstance(value, str) and not value.startswith('http'))

    for area in area_of_interest:
        if area in all_string:
            matches.append(row)

matches.sort(key=lambda x: x.get("_recency", ""), reverse=True)

with open("processed/area_matches.json", "w+") as area_matches_file:
    json.dump(matches, area_matches_file, indent=2)

