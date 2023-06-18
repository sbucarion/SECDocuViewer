from django.shortcuts import render
from django.http import JsonResponse
import datetime
import sqlite3
import os 
import json

DB_PATH = os.getcwd().split("backend")[0] + "\\storage\\filing_data.sqlite3"


# Create your views here.
filing_style = {
    "3": "Form ",
    "4": "Form ",
    "424B2": "Form"
}


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
    

def clean_response(row):
    names = json.dumps(set(row[0].split(",")[:-1]), cls=SetEncoder)
    
    tickers = row[1].replace("FUND,", "").replace("UKNWN,","")
    if tickers == "":
        tickers = "No Tickers Found"
    
    
    date_time = datetime.datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')
    
    filing_type = row[3]
    filing_type = filing_style[filing_type] + filing_type if filing_type in filing_style else filing_type
    
    
    url = row[4]
    acc_no = row[5]
    
    return {"companies": names, "tickers": tickers, "time": date_time,"type": filing_type,"url": url,"acc_no": acc_no}

def get_latest_filings(request):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """SELECT reporter_company_name || '' || 
                    issuer_company_name || '' ||
                    subject_company_name || '' || 
                    filer_company_name || '' ||
                    filed_by_company_name AS merged_column1,

                    reporter_ticker || '' ||
                    issuer_ticker || '' ||
                    subject_ticker || '' || 
                    filer_ticker || '' ||
                    filed_by_ticker AS merged_column2,
                    
                    unix_number, filing_type, url, accession_number
        
    FROM filings
    ORDER BY unix_number
    LIMIT 10;"""


    cursor.execute(query)
    results = cursor.fetchall()

    cleaned_results = []
    test_dict = dict()
    for i, row in enumerate(results):
        cleaned_results.append(clean_response(row))
        test_dict[str(i)] = clean_response(row)

    package = json.dumps(cleaned_results)

    return JsonResponse(test_dict)