import re
import time
import requests
from bs4 import BeautifulSoup
import pdfkit
import sqlite3
import os 
from datetime import datetime
from sec_cik_mapper import StockMapper


def get_all_filings(soup):
    #Go through all filings with html text and accerssion
    filings = []
    for row in soup.findAll("tr"):
        if "Accession Number" in row.text:
            filings.append(row)
            
    return filings


def get_acc_no(filing):
    text = filing.findAll('td')[2].text
    
    # Extract the accession number using regex
    match = re.search(r"Accession Number: (\d{10}-\d{2}-\d{6})", text)
    if match:
        accession_number = match.group(1)
        return (accession_number)


def get_filing_time(filing):
    time_data = filing.findAll('td')[3]
    date = time_data.contents[0]
    time = time_data.contents[2]
    
    datetime_obj = datetime.strptime(date + " " + time, '%Y-%m-%d %H:%M:%S')
    unix_time = int(datetime_obj.timestamp())
    
    return unix_time


def get_filing_detail_link(filing):
    for links in filing.findAll('a'):
        href = links['href']

        if ".htm" in href:
            return r"http://sec.gov" + href

        
def get_filing_file_links(filing_div, main_file_type):
    links = {
        "main": "",
        "supporting": []
    }

    for row in filing_div.find('table').findAll('tr'):
        if row.find('th') == None:
            try:

                file_type = row.findAll('td')[3].text
                if file_type == '\xa0':
                    continue

                link = "http://sec.gov" + row.find('a')['href']
                
                if file_type == main_file_type and links["main"] == "":
                    links["main"] = link

                if file_type != main_file_type:
                    links["supporting"].append(link)
                    
                    

            except:
                continue
                
    return links 
        

def get_filers_data(filers_div):
    filers_info = []
    
    for filer in filers_div.findAll('div', id='filerDiv'):
        filer_info = filer.find("span", "companyName").text.lower()

        filer_cik = re.search(r"cik:\s+(\d+)", filer_info).group(1)
        filer_name = re.search(r'^(.*?)\s*\(', filer_info).group(1)

        try:
            filer_type = re.findall(r'\((reporting|issuer|subject|filer|filed by|)\)', filer_info)[0]

        except IndexError as e:
            print(filer_cik, filer_name)
            continue
            
        if filer_type == "filed by":
            filer_type = "filed_by"
    
        
        try:
            tickers = list(mapper.cik_to_tickers[filer_cik])
            
            if len(tickers) == 1:
                ticker = tickers[0]
                
            else:
                ticker = "UNKWN"

        except KeyError as e:
            ticker = "FUND"


        filer_info = {
            "cik": filer_cik,
            "company_name": filer_name,
            "filer_ticker": ticker,
            "filer_type": filer_type,
        }
        
        filers_info.append(filer_info)


    return filers_info
        
        
        
def get_filing_metadata(filing_detail_link, filing_type):
    """returns meta data (report cik, and name) and links to files to download later"""
    filing_detail_request = requests.get(filing_detail_link, headers=headers).text
    filing_detail_soup = BeautifulSoup(filing_detail_request, "html.parser")
    
    #Location of filers info and filing pdf links 
    filing_detail_data = filing_detail_soup.find('div', id='contentDiv')
    
    #Extract the people/entites filing the form/report
    filers_data = get_filers_data(filing_detail_data)
    
    #Extract the links to the pdfs from the details page
    filing_forms = filing_detail_data.findAll('div', id='formDiv')[1] #where main file and supporting docs are
    filing_file_links = get_filing_file_links(filing_forms, filing_type)

    
    return filers_data, filing_file_links

    
def save_data_to_database(filing_metadata, cursor, connection, project_dir):
    #may be some of the worst code ever written
    ##need to decide if i want to actually store filers based off issuer/reporter etc or 
    #just lump them all together
    
    #### GARBAGE FROM HERE ######
    filer_company_name = filer_cik = filer_ticker = ""
    filed_by_company_name = filed_by_cik = filed_by_ticker = ""
    subject_company_name = subject_cik = subject_ticker = ""
    issuer_company_name = issuer_cik = issuer_ticker = ""
    reporter_company_name = reporter_cik = reporter_ticker = ""

    filers = metadata['filers']   
    for filer in filers:

        if filer['filer_type'] == "filer":
            filer_company_name += filer['company_name'] + ","
            filer_cik += filer['cik'] + ","
            filer_ticker += filer['filer_ticker'] + ","

        if filer['filer_type'] == "filed_by":
            filed_by_company_name += filer['company_name'] + ","
            filed_by_cik += filer['cik'] + ","
            filed_by_ticker += filer['filer_ticker'] + ","


        if filer['filer_type'] == "subject":
            subject_company_name += filer['company_name'] + ","
            subject_cik += filer['cik'] + ","
            subject_ticker += filer['filer_ticker'] + ","


        if filer['filer_type'] == "issuer":
            issuer_company_name += filer['company_name'] + ","
            issuer_cik += filer['cik'] + ","
            issuer_ticker += filer['filer_ticker'] + ","


        if filer['filer_type'] == "reporting":
            reporter_company_name += filer['company_name'] + ","
            reporter_cik += filer['cik'] + ","
            reporter_ticker += filer['filer_ticker'] + ","
    
    
    insert_sql = '''
    INSERT INTO filings (
        accession_number,
        unix_number,
        filing_type,
        reporter_cik,
        reporter_company_name,
        reporter_ticker,
        subject_cik,
        subject_company_name,
        subject_ticker,
        issuer_cik,
        issuer_company_name,
        issuer_ticker,
        filer_cik,
        filer_company_name,
        filer_ticker,
        filed_by_cik,
        filed_by_company_name,
        filed_by_ticker,
        url) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    
    
    cursor.execute(insert_sql, (
        metadata["accession_no"],
        metadata["unix"],
        metadata["filing_type"],
        reporter_cik,
        reporter_company_name,
        reporter_ticker,
        subject_cik,
        subject_company_name,
        subject_ticker,
        issuer_cik,
        issuer_company_name,
        issuer_ticker,
        filer_cik,
        filer_company_name,
        filer_ticker,
        filed_by_cik,
        filed_by_company_name,
        filed_by_ticker,
        metadata["url"]
    ))
    
    connection.commit()
    
    
    #### TO HERE ####
    #Gets the job done so may not need to refactor
    
    storage_dir = project_dir + "\\storage\\filings\\"

    try:
        os.mkdir(storage_dir + metadata['accession_no']) #Creates storage file for whole filing
    except:
        return


    file_path = storage_dir + metadata['accession_no']
    
    if len(metadata['filing_links']['supporting']) > 0:
        os.mkdir(file_path+ "\\supporting")
        
    main_file = metadata['filing_links']['main']
    if "ix?doc=" in main_file:
        main_file = main_file.split("/ix?doc=")[0]+main_file.split("/ix?doc=")[-1] #Combine into one variable so we dont split twice


    supporting_files = metadata['filing_links']['supporting']
    
    path_wkhtmltopdf = project_dir + "\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    
    pdfkit.from_url(main_file, file_path+"\\main_file.pdf", configuration=config)
    
    return

    #disabling this code for now because some supporting files are so massive it take minutes to download
    #Next idea would be to send these to a different file in a queue where it downloads these alongside the main scraper
    #all can make it download like 5 at a time by creating multiple threads
    for i, file in enumerate(supporting_files):
        if "ix?doc=" in file:
            file = file.split("/ix?doc=")[0]+file.split("/ix?doc=")[-1]

        pdfkit.from_url(file, file_path+"\\supporting\\{}.pdf".format(str(i+1)), configuration=config)
    
    
    

def scraping_buffers(connection, cursor):
    cursor.execute("""SELECT accession_number, unix_number from filings""")
    query_results = cursor.fetchall()

    try:
        all_accession_numbers = {row[0] for row in query_results}
        max_unix_number = max({row[1] for row in query_results})
    
    except IndexError as e:
        max_unix_number = 0
        all_accession_numbers = []

    return max_unix_number, all_accession_numbers



headers = {
"User-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
}

latest_filings_url = \
r"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=&owner=include&count=100&action=getcurrent"


project_dir = os.getcwd().split("\\SEC_scraper")[0]

DB_PATH = project_dir + '\\storage\\filing_data.sqlite3'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

#max_unix, db_acc_nos = scraping_buffers(conn, cursor)
max_unix, db_acc_nos = scraping_buffers(conn, cursor)
mapper = StockMapper()

x = time.time()
#while True:
latest_filings = requests.get(latest_filings_url, headers=headers).text
filings_soup = BeautifulSoup(latest_filings, "html.parser")

# each filing is an individual 'tr' tag with metadata like acc_no, file type, and unix
# this var stores all filing rows by finding if "accession number" is in the rows text
filing_rows = get_all_filings(filings_soup)

for filing in filing_rows:
    time.sleep(0.20001) #SEC website allows only 10 requests a second
    metadata = dict()

    #converts the file timestamp (Y-m-d H:M:S) to unix for easy comparision
    #we will skip all files with less unix thnt max unix filing already found
    #because it means we have already scraped the file
    filing_unix_time = get_filing_time(filing)


    #means filing is older than most recently scrapped filing so it means weve already scraped this filing
    if max_unix >= filing_unix_time:
        continue

    #unique identifier for each filing (form 4s have same one for reporter and issuer)
    filing_acc_no = get_acc_no(filing)

    if filing_acc_no in db_acc_nos:
        continue
    
    #Get filing type here since its easier that on filing detail page
    filing_type = filing.findAll('td')[0].text


    #each link to filing on latest filing brings up a page with the file and supporting documents and meta data
    #the filing_detail_link takes us to that page to download metadata and the files
    filing_detail_link = get_filing_detail_link(filing)

    metadata = {
        "unix": filing_unix_time,
        "filing_type": filing_type,
        "accession_no": filing_acc_no,
        "url": filing_detail_link,
    }


    #Could wrap all of the above but too lazy


    #Now request filing detail page where we can scrape metadata, supporting docs and the main filing
    metadata["filers"], metadata["filing_links"] = get_filing_metadata(filing_detail_link, filing_type)

    #Now save to database and download pdfs
    #edge cases: if we have reporter and issuer should we combine files and ignore the reporter (usually a person)
    #save_data_to_database(filing_metadata)

    save_data_to_database(metadata, cursor, conn, project_dir)
    
    _, db_acc_nos = scraping_buffers(conn, cursor)
    #for looking up one company we have all files stored in folders with acc no as folder names
    #in database we have those accessions tied to the cik of the company as issuer, reporter or something else

    
max_unix, db_acc_nos = scraping_buffers(conn, cursor) #update new accession oumbers and get time of most recent filing
time.time() - x

conn.close()


#Current issue if file isnt convertable to pdf (jpg), then file will open but display nothing (so far .ht are safe)