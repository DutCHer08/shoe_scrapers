import json
import re
import random
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error

DB_HOST = "localhost"
DB_DATABASE = "drop_shop"
DB_USER = "drop-shop-acc"
DB_PASSWORD = "password123"

def scrape_product_properties(targetUrls):
    # KIX Data
    req = requests.get(targetUrls["kixify_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False)
    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type': 'application/ld+json'})

    stringData = str(rawData[1]) # Converting to String data
    regexedData = re.split("[<>]", stringData) # Removing the <script> tags from response
    jsonData = json.loads(regexedData[2]) # Loading desired data into json object

    # Init. dictionary that represents product
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
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"},
        verify=False)
    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type':'application/ld+json'})

    stringData = str(rawData[0])
    regexedData = re.split("[<>]", stringData)
    jsonData = json.loads(regexedData[2])

    regexedReleaseDate = re.split("(T)", (jsonData['releaseDate']))


    # Add variables to obj
    try:
        if (jsonData['offers']['lowPrice'] != 0):
            shoe_dict["lowestGoatPrice"] = (jsonData['offers']['lowPrice'])
        else:
            raise Exception("Price can't be zero")
    except:
        shoe_dict["lowestGoatPrice"] = (random.randint(2,10) * 100)
    shoe_dict["releaseDate"] = regexedReleaseDate[0]

    # FlightClub Data
    req = requests.get(targetUrls["fc_url"],
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False)

    # Locating and retrieving raw data from HTML
    page_content = req.text
    soup = BeautifulSoup(page_content, 'html.parser')
    rawData = soup.find_all('script', {'type':'application/ld+json'})

    stringData = str(rawData[1])
    regexedData = re.split("[<>]", stringData)
    jsonData = json.loads(regexedData[2])

    # Add variables to obj
    try:
        if (jsonData['offers']['lowPrice'] != 0):
            shoe_dict["lowestFcPrice"] = (jsonData['offers']['lowPrice'])
        else:
            raise Exception("Price can't be zero")
    except:
        shoe_dict["lowestFcPrice"] = (random.randint(2,10) * 100)

    shoe_dict["imgFilePath"] = (jsonData['image'])

    return shoe_dict

def get_mysql_query(action, shoe_props):
    if (action == "insert"):
        SQL_Insert_Query = "INSERT INTO products (brandName, productName, modelNum, productDescription, releaseDate, imgFilePath, collabName, lowestGoatPrice, lowestFcPrice, lowestKixPrice)"
        SQL_Insert_Query += "VALUES (\"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", {}, {}, {} )".format(
            shoe_props["brandName"],
            shoe_props["productName"].replace('"', '\\"'),
            shoe_props["modelNum"],
            shoe_props["productDescription"].replace('"', '\\"'),
            shoe_props["releaseDate"],
            shoe_props["imgFilePath"],
            shoe_props["collabName"], # this one comes from the original URL DB entry (but is initialized in the kixify section) - not scraped
            shoe_props["lowestGoatPrice"],
            shoe_props["lowestFcPrice"],
            shoe_props["lowestKixPrice"]
        )
        return SQL_Insert_Query
    elif (action == "update"):
        SQL_Update_Query = "UPDATE products SET brandName = \"{}\", productName = \"{}\", modelNum = \"{}\", productDescription = \"{}\", releaseDate = \"{}\", imgFilePath = \"{}\", collabName = \"{}\", lowestGoatPrice = {}, lowestFcPrice = {}, lowestKixPrice = {}"
        SQL_Update_Query = SQL_Update_Query.format(
            shoe_props["brandName"],
            shoe_props["productName"].replace('"', '\\"'),
            shoe_props["modelNum"],
            shoe_props["productDescription"].replace('"', '\\"'),
            shoe_props["releaseDate"],
            shoe_props["imgFilePath"],
            shoe_props["collabName"],
            shoe_props["lowestGoatPrice"],
            shoe_props["lowestFcPrice"],
            shoe_props["lowestKixPrice"]
        )
        SQL_Update_Query += " WHERE imgFilePath = \"{}\"".format(shoe_props["imgFilePath"])
        return SQL_Update_Query

try:
    connection = mysql.connector.connect(
        host = DB_HOST,
        database = DB_DATABASE,
        user = DB_USER,
        password = DB_PASSWORD,
        auth_plugin = "mysql_native_password" # not always required
    )
    SQL_Select_Query = "SELECT * FROM scraper_input"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(SQL_Select_Query)
    url_table_entries = cursor.fetchall()

    for row in url_table_entries:
        shoe_props = scrape_product_properties(row)
        try:
            query = get_mysql_query("insert", shoe_props)
            cursor.execute(query)
            connection.commit()
        except Error as e:
            if (e.errno == 1062): # Duplicate row detected - product already exists
                query = get_mysql_query("update", shoe_props)
                cursor.execute(query)
                connection.commit()

    if (connection.is_connected()):
        connection.close()
        cursor.close()

except Error as e:
    print("Error updating MySQL table", e)
