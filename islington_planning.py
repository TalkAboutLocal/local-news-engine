import requests
import lxml.html as html
from lxml.html.soupparser import fromstring
import os
import json
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

retries = Retry(total=18,
                backoff_factor=1)

headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0",
           "Host": "planning.islington.gov.uk",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.5",
           "DNT": "1",
           "Upgrade-Insecure-Requests": "1",
           "Cache-Control": "max-age=0"}

all_data = []
if os.path.exists('data/saved_islington_planning.json'):
    with open('data/saved_islington_planning.json' ) as saved:
        all_data = json.load(saved)

def fetch_list(date_from, date_to):
    print("saving list {} to {}".format(date_from, date_to))
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))

    response = s.get('http://planning.islington.gov.uk/northgate/planningexplorer/generalsearch.aspx', headers=headers)

    data = {'cboApplicationTypeCode': '',
     'cboDays': '1',
     'cboDevelopmentTypeCode': '',
     'cboMonths': '1',
     'cboSelectDateValue': 'DATE_RECEIVED',
     'cboStatusCode': '',
     'cboWardCode': '',
     'csbtnSearch': 'Search',
     'dateEnd': date_to,
     'dateStart': date_from,
     'edrDateSelection': '',
     'rbGroup': 'rbRange',
     'txtAgentName': '',
     'txtApplicantName': '',
     'txtApplicationNumber': '',
     'txtPostCode': '',
     'txtPropertyName': '',
     'txtPropertyNumber': '',
     'txtProposal': '',
     'txtSiteAddress': '',
     'txtStreetName': ''}


    content = html.document_fromstring(response.content)

    data["__VIEWSTATE"] = content.get_element_by_id("__VIEWSTATE").value
    data["__VIEWSTATEGENERATOR"] = content.get_element_by_id("__VIEWSTATEGENERATOR").value
    data["__EVENTVALIDATION"] = content.get_element_by_id("__EVENTVALIDATION").value

    headers["Referer"] = "http://planning.islington.gov.uk/northgate/planningexplorer/generalsearch.aspx"

    results = s.post('http://planning.islington.gov.uk/northgate/planningexplorer/generalsearch.aspx', headers=headers, data=data)
    new_url = results.url.replace("PS=10", "PS=100000")
    results = s.get(new_url, headers=headers)

    content = fromstring(results.content)


    all_rows = content.cssselect("tr")
    for row in all_rows:
        row_data = {}
        row_elements = row.cssselect("td")
        if not row_elements:
            continue
        row_data['href'] = ''.join(row_elements[0].cssselect("a")[0].attrib['href'].split())

        row_data['Application_number'] = row_elements[0].cssselect("a")[0].text

        row_data['Site Address'] = row_elements[1].text
        row_data['Development Description'] = row_elements[2].text
        row_data['Status'] = row_elements[3].text
        row_data['Date Registered'] = row_elements[4].text
        row_data['Decision'] = row_elements[5].text
        row_data['Done'] = False
        all_data.append(row_data)



if not all_data:
    fetch_list('01-01-2006', '31-12-2006')
    fetch_list('01-01-2007', '31-12-2007')
    fetch_list('01-01-2008', '31-12-2008')
    fetch_list('01-01-2009', '31-12-2009')
    fetch_list('01-01-2010', '31-12-2010')
    fetch_list('01-01-2011', '31-12-2011')
    fetch_list('01-01-2012', '31-12-2012')
    fetch_list('01-01-2013', '31-12-2013')
    fetch_list('01-01-2014', '31-12-2014')
    fetch_list('01-01-2015', '31-12-2015')
    fetch_list('01-01-2016', '31-12-2016')
    fetch_list('01-01-2017', '31-12-2017')

    with open('data/saved_islington_planning.json', 'w+') as saved:
        json.dump(all_data, saved, indent=4)

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=retries))
response = s.get('http://planning.islington.gov.uk/northgate/planningexplorer/generalsearch.aspx', headers=headers)

for num, record in enumerate(all_data):
    if record["Done"]:
        continue
    print("On number {} out of {}".format(num+1, len(all_data)))
    record_url = "http://planning.islington.gov.uk/Northgate/PlanningExplorer/Generic/" + record["href"]
    final_page = s.get(record_url, headers=headers)
    final_page_parsed = fromstring(final_page.content)
    all = final_page_parsed.cssselect("div > span")
    for page_item in all:
        record[page_item.text] = [a for a in page_item.getparent().itertext()][-1].strip()
    record["Done"] = True
    if num % 10 == 0:
        print("saved")
        try: 
            with open('data/saved_islington_planning.json', 'w+') as saved:
                json.dump(all_data, saved, indent=4)
        except:
            print("Caught exception")
            with open('data/saved_islington_planning.json', 'w+') as saved:
                json.dump(all_data, saved, indent=4)
            break

with open('data/saved_islington_planning.json', 'w+') as saved:
    json.dump(all_data, saved, indent=4)

    
