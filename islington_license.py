import requests
import lxml.html as html
from lxml.html.soupparser import fromstring
import os
import json
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

retries = Retry(total=18,
                backoff_factor=1)

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=retries))

headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0",
           "Host": "planning.islington.gov.uk",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.5",
           "DNT": "1",
           "Upgrade-Insecure-Requests": "1",
           "Cache-Control": "max-age=0"}


data = {'ddLiceType': '',
        'txtWord': '',
        'cboStreet': '',
        'cmdSearch': 'Search'
       }

response = s.get('http://planning.islington.gov.uk/Northgate/Online/EGov/License_Registers/Registers_Criteria.aspx', headers=headers)
content = html.document_fromstring(response.content)

data["__VIEWSTATE"] = content.get_element_by_id("__VIEWSTATE").value
data["__VIEWSTATEGENERATOR"] = content.get_element_by_id("__VIEWSTATEGENERATOR").value
data["__EVENTVALIDATION"] = content.get_element_by_id("__EVENTVALIDATION").value
headers["Referer"] = "http://planning.islington.gov.uk/Northgate/Online/EGov/License_Registers/Registers_Criteria.aspx"


results = s.post('http://planning.islington.gov.uk/Northgate/Online/EGov/License_Registers/Registers_Criteria.aspx', headers=headers, data=data)

new_url = results.url.replace("PS=10", "PS=100000")
results = s.get(new_url, headers=headers)

content = fromstring(results.content)
all_rows = content.cssselect("tr")

all_data = []
if os.path.exists('data/saved_islington_license.json'):
    with open('data/saved_islington_license.json' ) as saved:
        all_data = json.load(saved)

all_rows = content.cssselect("tr")
if not all_data:
    for row in all_rows:
        row_data = {}
        row_elements = row.cssselect("td")
        if not row_elements:
            continue
        row_data['href'] = ''.join(row_elements[0].cssselect("a")[0].attrib['href'].split())

        row_data['Location/Name'] = row_elements[0].cssselect("a")[0].text
        row_data['License Type'] = row_elements[1].text
        row_data['Status'] = row_elements[2].text
        row_data['Done'] = False
        all_data.append(row_data)

with open('data/saved_islington_license.json', 'w+') as saved:
    json.dump(all_data, saved, indent=4)


for num, record in enumerate(all_data):
    if record["Done"]:
        continue
    print("On number {} out of {}".format(num+1, len(all_data)))
    record_url = "http://planning.islington.gov.uk/Northgate/Online/EGov/License_Registers/" + record["href"]
    final_page = s.get(record_url, headers=headers)
    final_page_parsed = fromstring(final_page.content)
    all = final_page_parsed.cssselect("div > span")
    for page_item in all:
        existing_item = record.get(page_item.text)
        if existing_item: 
            if not isinstance(existing_item, list):
                record[page_item.text] = [existing_item]
            record[page_item.text].append([a for a in page_item.getparent().itertext()][-1].strip())
        else:
            record[page_item.text] = [a for a in page_item.getparent().itertext()][-1].strip()
    record["Done"] = True
    if num % 10 == 0:
        print("saved")
        try: 
            with open('data/saved_islington_license.json', 'w+') as saved:
                json.dump(all_data, saved, indent=4)
        except:
            print("Caught exception")
            with open('data/saved_islington_license.json', 'w+') as saved:
                json.dump(all_data, saved, indent=4)
            break
    
with open('data/saved_islington_license.json', 'w+') as saved:
    json.dump(all_data, saved, indent=4)
