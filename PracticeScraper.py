import mysql.connector
from mysql.connector import Error
from KixifyScraper import scrape

# Starting connection to mysql DB
try:
    connection = mysql.connector.connect(host='localhost',
                                         database='drop-shop',
                                         user='root',
                                         password='1234')
    sql_select_Query = "SELECT * FROM scraper_input where website_name = 'Kixify'"
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

except Error as e:
    print("Error reading data from MySQL table", e)
finally:
    if (connection.is_connected()):
        connection.close()
        cursor.close()
        print("MySQL connection is closed")

for url in urlList:
    targetUrl = url
    scrape(targetUrl)


