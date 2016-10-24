import requests
import lxml.etree as etree
import json
import os
from lxml.html.soupparser import fromstring

results = {}

if os.path.exists("data/saved_camden_license.json"):
    with open('data/saved_camden_license.json') as saved:
        data = saved.read()
        if data:
            results = json.loads(data)

#endpoint = 'http://search.camden.gov.uk/search?site=lra&client=lra&output=xml_no_dtd&entqr=0&access=p&getfields=*&filter=0&q=inmeta%3AWARD~{}&sort=date%3AD%3AS%3Ad1&num=1000&start={}'
endpoint = 'http://search.camden.gov.uk/search?site=lra&client=lra&output=xml_no_dtd&entqr=0&access=p&getfields=*&filter=0&q=inmeta:DRECEIVED:{}..{}&sort=date%3AD%3AS%3Ad1&num=1000&start=0'


def get_all(start_date, end_date):
    response = requests.get(endpoint.format(start_date, end_date))

    root = etree.fromstring(response.content)
    for element in root.cssselect('M'):
        count = element.text
        break
    else:
        return

    print(start_date + " " + end_date)
    print(count)

    for element in root.cssselect('R'):
        result = {"Done": False}
        for url_element in element.cssselect('U'):
            url = url_element.text
            break
        for url_element in element.cssselect('C'):
            cache_id = url_element.attrib['CID']
            break

        result['fetch_url'] = 'http://search.camden.gov.uk/search?q=cache:{}:{}&proxystylesheet=lra'.format(cache_id, url)
        results[url] = result

def get_data(document):
    data = {}

    overview = document.cssselect('div[name=overview]')
    current_topic = ""
    current_text = ""
    for item in overview[0].cssselect('td'): 
        if not item.text:
            continue
        text = item.text.strip()
        if text.endswith(":"):
            if current_text:
                data[current_topic] = current_text.strip()
            current_topic = text
            current_text = ""
        else:
            current_text = current_text + " " + text
    else:
        data[current_topic] = current_text

    other_secions = ['RelatedDocuments', 'RelatedLicences', 'RelatedActivities', 'RelatedConditions']
    for section in other_secions:
        data[section] = list(document.cssselect('div[name={}]'.format(section))[0].itertext())

    return data




if not results:
    all_months = []


    for year in range(2005, 2020):
        all_months.extend(['{}{:02}01'.format(a,b) for a, b in zip([year] * 12, range(1,13))])

    for range in zip(all_months[:-1], all_months[1:]):
        get_all(*range)

    with open('data/saved_camden_license.json', 'w+') as saved:
        json.dump(results, saved, indent=2)



for num, value in enumerate(results.values()):
    if value['Done']:
        continue
    print("Done {} out of {}".format(num + 1, len(results.values())))
    document = fromstring(requests.get(value['fetch_url']).content)
    data = get_data(document)
    value.update(data)
    value['Done']=True
    with open('data/saved_camden_license.json', 'w+') as saved:
        json.dump(results, saved, indent=2)
    import pprint; pprint.pprint(value)

print("Done")


