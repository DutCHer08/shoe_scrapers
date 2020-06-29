import json
import re
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
    rawData = soup.find_all('script', {'type':'application/ld+json'})

    # Converting to String data
    stringData = str(rawData[0])
    # print(stringData)

    # Removing the <script> tags from response
    regexedData = re.split("[<>]", stringData)
    print(regexedData[2])

    # Loading data into json object
    jsonData = json.loads(regexedData[2])

    # Dirty variables
    dirtyReleaseDate = (jsonData['releaseDate'])
    regexedReleaseDate = re.split("(T)", dirtyReleaseDate)

    brandName = (jsonData['brand'])


    # Clean variables for DB
    productName = (jsonData['model'])
    modelNum = (jsonData['sku'])
    lowPrice = (jsonData['offers']['lowPrice'])
    releaseDate = regexedReleaseDate[0]

    print(brandName + "\n" + productName + "\n" + modelNum + "\n" + lowPrice + "\n" + releaseDate)

# Example URL
scrape("https://www.goat.com/sneakers/yeezy-boost-350-v2-bred-cp9652")
