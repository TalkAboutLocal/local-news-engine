from jinja2 import Environment, FileSystemLoader 
import datetime
import json
import sys
env = Environment(loader=FileSystemLoader('templates'), autoescape=True)

if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    print('No version was specified on the commandline, piwik tracking may not work as intended.')
    version = ''


names_template = env.get_template('leads.html')
area_template = env.get_template('areas.html')
wards_template = env.get_template('explore.html')

with open("output/templates.js") as templatesjs:
    templates = templatesjs.read()

with open("processed/area_matches.json") as area_matches_file:
    area_matches = json.load(area_matches_file)

with open("processed/all_data.json") as all_data_file:
    all_data = json.load(all_data_file)

with open('output/areas.html', 'w+') as name_output:
    name_output.write(area_template.render(
        templates=templates,
        area_matches=area_matches,
        date=datetime.date.today().isoformat(),
        version=version,
    ))

with open('output/explore.html', 'w+') as ward_output, open("key_field_names.txt") as key_field_names_file:
    key_fields = list(set([key_field_name.strip() for key_field_name in key_field_names_file]))
    ward_output.write(wards_template.render(
        templates=templates,
        appearances=json.dumps(all_data),
        key_fields_json=json.dumps(key_fields),
        date=datetime.date.today().isoformat(),
        version=version,
    ))

with open("processed/interesting_names.json") as interesting_names_file:
    interesting_names = json.load(interesting_names_file)

with open('output/leads.html', 'w+') as name_output, open("key_field_names.txt") as key_field_names_file:
    key_fields = list(set([key_field_name.strip() for key_field_name in key_field_names_file]))
    name_output.write(names_template.render(
        templates=templates,
        interesting_names=interesting_names,
        interesting_names_json=json.dumps(interesting_names),
        date=datetime.date.today().isoformat(),
        key_fields_json=json.dumps(key_fields),
        version=version,
    ))

