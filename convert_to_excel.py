import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='actowiz',
    database='burger_king'
)

data = pd.read_sql('SELECT * from store_locators', conn)

data = data.drop(['id','page_no'], axis=1)

data.to_excel('burger_king_store_locations.xlsx', index=False)