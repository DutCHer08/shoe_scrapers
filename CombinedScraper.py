import json
import re
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

def scrape(targetUrls):
    # KIX Data
    # Setting up web request
    req = requests.get(targetUrls["kixify_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False)
    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type': 'application/ld+json'})
    # Converting to String data
    stringData = str(rawData[1])
    # Removing the <script> tags from response
    regexedData = re.split("[<>]", stringData)
    # Loading data into json object
    jsonData = json.loads(regexedData[2])

    # Clean variables for DB
    shoe_dict: Dict[str, Any] = {
        "collabName": targetUrls["collab_name"],
        "brandName": (jsonData['brand']['name']),
        "productName" : (jsonData['name']),
        "modelNum" : (jsonData['mpn']),
        "lowestKixPrice" : (jsonData['offers']['lowPrice']),
        "productDescription" : (jsonData['description']),
    }

    # GOAT Data
    req = requests.get(targetUrls["goat_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False)
    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type':'application/ld+json'})

    # Converting to String data
    stringData = str(rawData[0])

    # Removing the <script> tags from response
    regexedData = re.split("[<>]", stringData)

    # Loading data into json object
    jsonData = json.loads(regexedData[2])

    # Dirty variables
    dirtyReleaseDate = (jsonData['releaseDate'])
    regexedReleaseDate = re.split("(T)", dirtyReleaseDate)

    brandName = (jsonData['brand'])


    # Add variables to obj
    shoe_dict["lowestGoatPrice"] = (jsonData['offers']['lowPrice'])
    shoe_dict["releaseDate"] = regexedReleaseDate[0]

    # FlightClub Data
    req = requests.get(targetUrls["fc_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False)

    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type':'application/ld+json'})

    # Converting to String data
    stringData = str(rawData[1])

    # Removing the <script> tags from response
    regexedData = re.split("[<>]", stringData)
    # Loading data into json object
    jsonData = json.loads(regexedData[2])

    # Add variables to obj
    shoe_dict["lowestFcPrice"] = (jsonData['offers']['lowPrice'])
    shoe_dict["imgFilePath"] = (jsonData['image'])

    return shoe_dict

# Starting connection to mysql DB
try:
    connection = mysql.connector.connect(host='localhost',
                                         database='drop_shop',
                                         user='drop-shop-acc',
                                         password='password123',
                                         auth_plugin='mysql_native_password')
    sql_select_Query = "SELECT * FROM scraper_input"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()

    for row in records:
        shoe_props = scrape(row)
        # print(shoe_props)

        SQL_Insert_Query = "INSERT INTO products (brandName, productName, modelNum, productDescription, releaseDate, imgFilePath, collabName, lowestGoatPrice, lowestFcPrice, lowestKixPrice)"
        SQL_Insert_Query += "VALUES (\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", {}, {}, {} )".format(
                shoe_props["brandName"],
                shoe_props["productName"],
                shoe_props["modelNum"],
                shoe_props["productDescription"],
                shoe_props["releaseDate"],
                shoe_props["imgFilePath"],
                shoe_props["collabName"], # this one comes from the original URL DB entry (but is initialized in the kixify section) - not scraped
                shoe_props["lowestGoatPrice"],
                shoe_props["lowestFcPrice"],
                shoe_props["lowestKixPrice"],
            )
        # print(SQL_Insert_Query)
        cursor.execute(SQL_Insert_Query)
        connection.commit()

    if (connection.is_connected()):
        connection.close()
        cursor.close()
        print("MySQL connection is closed")

except Error as e:
    print("Error reading data from MySQL table", e)
