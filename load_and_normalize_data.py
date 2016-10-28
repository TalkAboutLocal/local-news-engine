import json
import csv
from dateutil import parser
import datetime
import requests
from collections import defaultdict

import re
postcode_re = "((GIR|[A-Za-z][0-9][0-9]?|[A-Za-z][A-Za-z][0-9][0-9]?|[A-Za-z][0-9][A-Za-z]|[A-Za-z][A-Za-z][0-9][A-Za-z])[ ]?([0-9][A-Za-z]{2}))"

postcode_re_just_letter = "[A-Za-z][A-Za-z][0-9][A-Za-z]"

def clean_name(name):
    name = name.lower()
    for title in ("mr", "ms", "mrs", "miss"):
        name = name.replace(title + " ", "")
        name = name.replace(title + ". ", "")
    return name.strip().lower()

def find_postcodes(data):
    find_postcode = re.findall(postcode_re, data) 

    postcodes = []

    for postcode in find_postcode:
        postcode_object = {}
        postcode_object['full_postcode'] = postcode[1] + ' ' + postcode[2]
        postcode_object['district_postcode'] = [postcode[1]]

        postcode_just_letter = re.findall(postcode_re_just_letter, postcode_object['district_postcode'][0])
        if postcode_just_letter:
            postcode_object['district_postcode'].append(postcode_just_letter[0][:-1])

        postcodes.append(postcode_object)
    return postcodes



def load_courts_data():
    with open('courts_data/courts.json') as courts:
        courts_data = json.load(courts)

    for row in courts_data:
        row["_postcode_districts"] = set(row['possible_postcode_districts'])
        address = row.get('address')
        postcodes = find_postcodes(address)
        row['_postcodes'] = set()
        for item in postcodes:
            row['_postcodes'].add(item['full_postcode'])
            row["_postcode_districts"].update(item['district_postcode'])
        row['_postcodes'] = list(row['_postcodes'])
        row["_postcode_districts"] = list(row["_postcode_districts"])
        row["_names"] = [clean_name(row["name"])]
        row["_recency"] = parser.parse(row['date'], dayfirst=True).isoformat()
        row["_source"] = "Courts"
        row["_source_type"] = "Courts"

    return courts_data

def load_camden_planning_data():
    with open('data/mcgw-i4rx.json') as camden_planning:
        camden_planning_data = json.load(camden_planning)

    for row in camden_planning_data:
        row['_postcodes'] = set()
        row["_postcode_districts"] = set()
        address = row.get('development_address')
        postcodes = find_postcodes(address)
        for item in postcodes:
            row['_postcodes'].add(item['full_postcode'])
            row["_postcode_districts"].update(item['district_postcode'])

        row['_postcodes'] = list(row['_postcodes'])
        row["_postcode_districts"] = list(row["_postcode_districts"])
        row["_source"] = "Camden Planning"
        row["_source_type"] = "Planning"

        applicant_name = row.get('applicant_name')
        if applicant_name:
            row["_names"] = [clean_name(applicant_name)]

        row["_recency"] = row['system_status_change_date']

    return camden_planning_data

def load_camden_license_data():
    with open('data/saved_camden_license.json') as camden_licence:
        camden_license_data = json.load(camden_licence)

    camden_license_list = list(camden_license_data.values())

    for row in camden_license_list:
        row['_postcodes'] = set()
        row["_postcode_districts"] = set()

        address = row.get('Premises address:')
        if address:
            postcodes = find_postcodes(address)
            for item in postcodes:
                row['_postcodes'].add(item['full_postcode'])
                row["_postcode_districts"].update(item['district_postcode'])
        row['_postcodes'] = list(row['_postcodes'])
        row["_postcode_districts"] = list(row["_postcode_districts"])

        row["_source"] = "Camden License"
        row["_source_type"] = "License"

        row["_names"] = set()
        for key in ('Applicant:', 'Correspondant:', 'Director:', 'Employee:'):
            name = row.get(key)
            if name:
                row["_names"].add(clean_name(name.replace('  ',' ')))
        row["_names"] = list(row["_names"])
        datetimes = []
        for key, value in row.items():
            if isinstance(value, list):
                new_list = [item for item in value if item.strip()]
                row[key] = new_list
            if not isinstance(value, str):
                continue
            try:
                datetimes.append(datetime.datetime.strptime(value, '%d/%m/%Y'))
            except ValueError:
                pass

        row["_recency"] = max(datetimes).isoformat()


    return camden_license_list

def load_islington_planning_data():

    with open('data/saved_islington_planning.json') as islington_planning:
        islington_planning_data = json.load(islington_planning)

    for row in islington_planning_data:
        row['_postcodes'] = set()
        row["_postcode_districts"] = set()
        address = row.get('Site Address')
        if address:
            postcodes = find_postcodes(address)
            for item in postcodes:
                row['_postcodes'].add(item['full_postcode'])
                row["_postcode_districts"].update(item['district_postcode'])

        row['_postcodes'] = list(row['_postcodes'])
        row["_postcode_districts"] = list(row["_postcode_districts"])
        row["_source"] = "Islington Planning"
        row["_source_type"] = "Planning"

        applicant_name = row.get('Applicant')
        if applicant_name:
            row["_names"] = [clean_name(applicant_name)]

        datetimes = []
        for key, value in row.items():
            if isinstance(value, list):
                new_list = [item for item in value if item.strip()]
                row[key] = new_list
            if not isinstance(value, str):
                continue
            try:
                datetimes.append(datetime.datetime.strptime(value, '%d-%m-%Y'))
            except ValueError:
                pass
        if datetimes:
            row["_recency"] = max(datetimes).isoformat()

    return islington_planning_data


def load_islington_license_data():
    with open('data/saved_islington_license.json') as islington_license:
        islington_license_data = json.load(islington_license)
    for row in islington_license_data:
        row['_postcodes'] = set()
        row["_postcode_districts"] = set()
        address = row.get('Licence for')
        if address:
            postcodes = find_postcodes(address)
            for item in postcodes:
                row['_postcodes'].add(item['full_postcode'])
                row["_postcode_districts"].update(item['district_postcode'])

        row['_postcodes'] = list(row['_postcodes'])
        row["_postcode_districts"] = list(row["_postcode_districts"])
        row["_source"] = "Islington License"
        row["_source_type"] = "License"

        applicant_name = row.get('Applicant')
        if applicant_name:
            row["_names"] = [clean_name(applicant_name)]

        datetimes = []
        for key, value in row.items():
            if isinstance(value, list):
                new_list = [item for item in value if item.strip()]
                row[key] = new_list
            if not isinstance(value, str):
                continue
            if len(value) < 8:
                continue
            try:
                date = parser.parse(value)
                if date > datetime.datetime.now():
                    continue
                datetimes.append(parser.parse(value))
            except ValueError:
                pass
        if datetimes:
            row["_recency"] = max(datetimes).isoformat()

    return islington_license_data


def load_rest_people(all_names, all_data):
    for item in all_data:
        names = item.get("_names")
        if names:
            for name in names:
                all_names[name].append({"source": item["_source"], "data": item, "source_type": item["_source_type"]})


def load_will_people(all_names):
    with open("data/will_people_of_interest.json") as will_data:
        will_people_of_interest = json.load(will_data)
        for source, name in will_people_of_interest:
            all_names[clean_name(name)].append({"source": source, "source_type": "Name", "data": {}})

def load_camden_journal_data(all_names):
    with open('data/saved_camdennewjournal_entities.json') as camden_journal:
        camden_journal_data = json.load(camden_journal)

    for key, value in camden_journal_data.items():
        for data in value:
            all_names[clean_name(key)].append({"source": "Camden New Journal", 
                                               "source_type": "Name",
                                               "data": data})


courts_data = load_courts_data()
#import pprint; pprint.pprint(courts_data)

camden_planning_data = load_camden_planning_data()
#import pprint; pprint.pprint(camden_planning_data[:100])

camden_license_data = load_camden_license_data()
#import pprint; pprint.pprint(camden_license_data[:100])

islington_planning_data = load_islington_planning_data()
#import pprint; pprint.pprint(islington_planning_data[:100])

islington_license_data = load_islington_license_data()

all_data = courts_data + camden_planning_data + camden_license_data + islington_planning_data + islington_license_data 

all_names = defaultdict(list)
load_camden_journal_data(all_names)
load_will_people(all_names)
load_rest_people(all_names, all_data)

