from jinja2 import Environment, FileSystemLoader 
import json
import sys
env = Environment(loader=FileSystemLoader('templates'), autoescape=True)

if len(sys.argv) > 1:
    user = sys.argv[1]
else:
    user = 'test'

names_template = env.get_template('names.html')
area_template = env.get_template('areas.html')

with open("output/templates.js") as templatesjs:
    templates = templatesjs.read()

with open("processed/area_matches.json") as area_matches_file:
    area_matches = json.load(area_matches_file)

with open('output/areas.html', 'w+') as name_output:
    name_output.write(area_template.render(templates=templates, area_matches=area_matches, user=user))

with open("processed/interesting_names.json") as interesting_names_file:
    interesting_names = json.load(interesting_names_file)

with open('output/names.html', 'w+') as name_output:
    name_output.write(names_template.render(templates=templates, interesting_names=interesting_names, interesting_names_json=json.dumps(interesting_names), user=user))

