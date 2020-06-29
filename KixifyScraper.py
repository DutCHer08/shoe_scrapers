import json
import re
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

def scrape(targetUrl):
    # Setting up web request
    scrapingUrl = targetUrl
    req = requests.get(scrapingUrl,
                       headers={"User-Agent": "Mozilla/5.0"},
                       verify=False)

    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type': 'application/ld+json'})

    # Converting to String data
    stringData = str(rawData[1])
    # print(stringData)

    # Removing the <script> tags from response
    regexedData = re.split("[<>]", stringData)
    print(regexedData[2])

    # Loading data into json object
    jsonData = json.loads(regexedData[2])

    # Clean variables for DB
    shoe_dict: Dict[str, Any] = {
        "brandName": (jsonData['brand']['name']),
        "productName" : (jsonData['name']),
        "modelNum" : (jsonData['mpn']),
        "lowPrice" : (jsonData['offers']['lowPrice']),
        "description" : (jsonData['description'])
    }
    return shoe_dict

# Starting connection to mysql DB
try:
    connection = mysql.connector.connect(host='localhost',
                                         database='drop-shop',
                                         user='root',
                                         password='1234')
    sql_select_Query = "SELECT * FROM scraper_input where website_name LIKE 'Kix%'"
    # MySQLCursorDict creates a cursor that returns rows as dictionaries
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    #print("Fetching each row using column name")

    urlList = []
    for row in records:
        urlColumn = row["url"]
        urlList.append(urlColumn)
    #print(urlList)

    # running scrape script
    for url in urlList:
        targetUrl = url
        shoe_properties = scrape(targetUrl)
        #sql_update_Query = ""

except Error as e:
    print("Error reading data from MySQL table", e)
finally:
    if (connection.is_connected()):
        connection.close()
        cursor.close()
        print("MySQL connection is closed")