import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import datetime

def wait_for(driver, xpath):
    try:
        WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.XPATH, xpath))
        return True
    except:
        print("TIMEOUT")
        return False

def click(driver, elem):
    driver.execute_script("arguments[0].click();", elem)
    # elem.click()

def convert(t):
    raw = str(t).split(".")[0].split(" ")
    return "%sT%s-05:00" % (raw[0], raw[1])


# Useless data for: S-30th, S-M. D-R also just has temp and tidal elevation
# Tacony-Castor also 
SITES = ["01474500", "01474501", "01473800", "01474000", "01467042", "01467048", "01465798", "014670261", "01467059", \
    "01467200", "01467086", "01467087", "01475530", "01475548"]
SITE_NAMES = ["Schuylkill-Fairmount", "Schuylkill-30th", "Schuylkill-Manayunk", "Wissahickon", "Pennypack-Pine", \
    "Pennypack-Rhawn", "Poquessing", "Delaware-Pennypack", "Delaware-Riverton", "Delaware-Penn", "Tacony-Adams", \
        "Tacony-Castor", "Cobbs-Highway", "Cobbs-Moriah"]
DAY_THRESH = 6

start_date = convert(datetime.datetime.now() - datetime.timedelta(days = 5))
end_date = convert(datetime.datetime.now())

table_id = "div[@class = 'select-time-series-container']"
div_id = "div[@class = 'parameter-row-info-container']"

def get_raw_attrs(site):
    driver = webdriver.Chrome()
    driver.get("https://waterdata.usgs.gov/monitoring-location/%s/" % (site, ))
    wait_for(driver, "//%s" % (table_id))

    raw_attrs = []

    wait_for(driver, "//%s//%s" % (table_id, div_id))
    for x in driver.find_elements(By.XPATH, "//%s//%s" % (table_id, div_id)):
        sub_soup = BeautifulSoup(x.get_attribute("outerHTML"), features="html.parser")
        dates = sub_soup.find("div", {"class", "period-of-record-text"}).text
        info = sub_soup.find("label")
        raw_attrs.append((dates, info.attrs['for'], info.text))
    return raw_attrs

def process_site(site):
    raw_attrs = get_raw_attrs(site)
    viable_data = []
    for attr in raw_attrs:
        (start, end) = attr[0].split(" to ")
        sd, ed = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
        diff = ed - sd
        if (diff.days < DAY_THRESH):
            continue
        if (len(attr[1].split("-")[-1]) != 5):
            continue
        viable_data.append((attr[1].split("-")[-1], attr[2]))
    parameter = ",".join([vd[0] for vd in viable_data])
    
    url = "https://waterservices.usgs.gov/nwis/iv/?sites=%s&parameterCd=%s&startDT=%s&endDT=%s&siteStatus=all&format=rdb" % (site, parameter, start_date, end_date)
    driver = webdriver.Chrome()
    driver.get(url)
    data_table = BeautifulSoup(driver.page_source, features="html.parser").find('pre').text
    f_name = "Data/%s_%s.txt" % (site, end_date)
    f = open(f_name, "w")

    i = 0
    f.write("\t".join([vd[0] for vd in viable_data]) + "\n")
    for row in data_table.split("\n")[:-1]:
        if row[0] == "#":
            continue
        if i >= 2:
            f.write(row + "\n")
        i += 1
    f.close()


for site, site_name in zip(SITES, SITE_NAMES):
    print("Processing: %s, aka. %s" % (site, site_name))
    try:
        process_site(site)
        print("*****")
    except:
        print("error")