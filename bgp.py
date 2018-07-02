#!/usr/bin/env python
import os  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options 
from time import sleep
from bs4 import BeautifulSoup
import re
from optparse import OptionParser

def get_choice(description):
    """
    Take a description string and prompt user if the company is in scope.

    Returns:
        bool - If the user indicated description should be in scope.
    """
    yes = ['yes', 'y', '']
    no = ['n', 'no']
    choices = yes + no
    prompt = "Is {} part of your scope? [y/n, default yes]: ".format(description)
    choice = input(prompt)
    while choice.strip().lower() not in choices:
        print("Error: You submitted {}, but must be one of {}.".format(choice, ", ".join(choices)))
        choice = input(prompt)
    choice = choice.strip().lower()
    return choice in yes

def process_pages(pages, driver):
    """
    Takes a list of string urls, pages, and a chrome driver object
    to then fetch and parse.

    If the URL matches with /AS####, then we search for IPV4 prefixes
    and add them to the results.

    If the URL matches with /net/CIDR, then we add the CIDR and search
    for new DNS names.

    Parameters:
        pages - list of strings for the bgp.he.net service
        driver - Chrome selenium driver object

    Returns:
        dict - Dictionary of the results. Should be of the form:

        results = {
            "net_blocks": ["CIDR1", "CIDR2"],
            "domain_names": ["uber.com", "uberinternal.com", ...]
        }
    """
    results = {"net_blocks": [], "domains": []}
    count = 0
    while pages:
        # The url
        url = pages[0]
        driver.get(url)
        try:
            if re.findall("AS[0-9]+", url):
                # The AS# page, search for IPV4
                # Then add those IPv4 pages to pages to process
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                links = soup.find_all('a', href=True)
                hrefs = ["http://bgp.he.net/{}".format(x['href']) for x in links if "/net/" in x['href']]
                cidrs = ["/".join(url.split("/")[-2:]) for url in hrefs]
                for cidr in cidrs:
                    if cidr not in results['net_blocks']:
                        results['net_blocks'].append(cidr)
                for href in hrefs:
                    if href not in pages:
                        #print("Found new link: {}".format(href))
                        pages.append(href)

            elif re.findall("/net/", url):
                # Add IPV4 range from url to results
                # Parse link for DNS entries
                cidr = "/".join(url.split("/")[-2:])
                if cidr not in results['net_blocks']:
                    results['net_blocks'].append(cidr)
                if "No DNS Records Found" not in driver.page_source and "did not return any results" not in driver.page_source:
                    dns_table = driver.find_element_by_id("dns")
                    soup = BeautifulSoup(dns_table.get_attribute("outerHTML"), "html.parser")
                    tbody = soup.find('tbody')
                    rows = tbody.find_all("tr")
                    for row in rows:
                        dns_name = None
                        cells = row.find_all("td")
                        ptr = cells[1]
                        a_record = cells[-1]
                        dns_link = ptr.find("a")
                        a_record_link = a_record.find("a")
                        if dns_link:
                            dns_name = dns_link.contents[0]
                        if a_record_link:
                            dns_name = a_record_link.contents[0]
                        if dns_name and dns_name not in results['domains']:
                            #print("Discovered new DNS name: {}".format(dns_name))
                            results['domains'].append(dns_name)
            else:
                print("Unknown link type, cannot parse.")
            count += 1
            print("Parsed {} page.".format(count))
        except Exception as e:
            if "You have reached your query limit" in driver.page_source:
                print("Query limit reached. Breaking and writing results.")
                break
            else:
                print("Oh no! An issue occurred. Please submit an issue on the Github repository with the debug.png and debug.html files.")
                print("Error: {}".format(e))
                driver.save_screenshot('debug.png')
                with open('debug.html', 'w') as f:
                    f.write(driver.page_source)
                break
        pages.pop(0)
    return results

def main():
    usage = """%prog -c "Company Name Here" -o "outprefix"

██████╗  ██████╗ ██████╗     ██╗      ██████╗  ██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗██╔════╝ ██╔══██╗    ██║     ██╔═══██╗██╔═══██╗██║ ██╔╝██║   ██║██╔══██╗
██████╔╝██║  ███╗██████╔╝    ██║     ██║   ██║██║   ██║█████╔╝ ██║   ██║██████╔╝
██╔══██╗██║   ██║██╔═══╝     ██║     ██║   ██║██║   ██║██╔═██╗ ██║   ██║██╔═══╝ 
██████╔╝╚██████╔╝██║         ███████╗╚██████╔╝╚██████╔╝██║  ██╗╚██████╔╝██║     
╚═════╝  ╚═════╝ ╚═╝         ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝    


Author: Dwight Hohnstein (@djhohnstein)
"""
    parser = OptionParser(usage)
    parser.add_option("-c", "--company", dest="company", help="Comany to search registered addresses in BGP. Required.")
    parser.add_option("-o", "--output-prefix", dest="prefix", help="Write results to two files, one for IPs and one for domains, with the prefix passed. Final file will be named $prefix.ips.txt and $prefix.domains.txt")
    (options, args) = parser.parse_args()
    if not options.company:
        print(parser.usage)
        print("Requires a company (-c) to search for.")
        exit(1)

    chrome_options = Options()  
    chrome_options.add_argument("--headless")  
    chrome_options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary' 

    driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), chrome_options=chrome_options)  
    base_url = "http://bgp.he.net"
    driver.get(base_url)

    while "Your ISP is" not in driver.page_source:
        print("Waiting for BGP to validate browser...")
        sleep(5)
    searchbox = driver.find_element_by_id("search_search")  

    # Enter search term
    searchbox.send_keys(options.company)  
    searchbox.send_keys(Keys.RETURN)

    while "Please wait while we validate your browser." in driver.page_source:
        print("Waiting for BGP to validate on search...")
        sleep(5)
    if "did not return any results" in driver.page_source:
        print("No results returned.")
        driver.close()
        exit(0)
    else:
        print("Results found!")

    searchdata = driver.find_element_by_id("search")
    searchdata_html = searchdata.get_attribute("outerHTML")
    soup = BeautifulSoup(searchdata_html, "html.parser")
    table = soup.find('table')
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')

    # Variables to track descriptors that are in scope
    scoped = []
    not_scoped = []

    # Variable to track which pages to parse, should be paths from the base url
    pages_to_process = []

    for row in rows:
        result, description = row.find_all('td')
        contents = description.contents
        if contents:
            in_scope = False
            if contents[0] in not_scoped:
                pass
            elif contents[0] in scoped:
                in_scope = True
            else:
                in_scope = get_choice(contents[0])
            if in_scope:
                result_contents = result.contents
                scoped.append(contents[0])
                pages_to_process.append("{}{}".format(base_url, result_contents[0]['href']))
    
    if pages_to_process:
        print("Parsing results...")
        results = process_pages(pages_to_process, driver)
        print("CIDRs belonging to {}:".format(options.company))
        print("------------------------")
        print("\n".join(results["net_blocks"]))
        print()
        print("Domain names discovered:")
        print("------------------------")
        print("\n".join(results["domains"]))
        if options.prefix:
            with open("{}.ips.txt".format(options.prefix), "w") as f:
                f.write("\n".join(results["net_blocks"]))
            with open("{}.domains.txt".format(options.prefix), "w") as f:
                f.write("\n".join(results["domains"]))

    driver.close()

if __name__ == "__main__":
    main()
