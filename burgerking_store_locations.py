import requests
from lxml import html
import mysql.connector
import sys

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='actowiz',
    database='burger_king'
)

cur = conn.cursor()

cookies = {
    '_ga_KQE6QVSPD1': 'GS1.1.1722419101.1.1.1722420597.0.0.0',
    '_gcl_au': '1.1.1016205060.1722420598',
    '_gid': 'GA1.2.109550547.1722420599',
    '_gat_gtag_UA_196801382_1': '1',
    '_gat_UA-196801382-1': '1',
    '_ga_51NSXH673Q': 'GS1.1.1722420598.1.0.1722420598.0.0.0',
    '_ga': 'GA1.1.1625532950.1722419101',
    '_fbp': 'fb.1.1722420599606.761629277674007115',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    # 'cookie': '_ga_KQE6QVSPD1=GS1.1.1722419101.1.1.1722420597.0.0.0; _gcl_au=1.1.1016205060.1722420598; _gid=GA1.2.109550547.1722420599; _gat_gtag_UA_196801382_1=1; _gat_UA-196801382-1=1; _ga_51NSXH673Q=GS1.1.1722420598.1.0.1722420598.0.0.0; _ga=GA1.1.1625532950.1722419101; _fbp=fb.1.1722420599606.761629277674007115',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
}


def db_store(data, status=None):
    if status == 'SUCCESS':
        query = 'insert into page_data(page_no, status, no_of_records) values (%s, %s, %s)'
        cur.execute(query, (data), )
        conn.commit()
    else:
        query = 'insert ignore into store_locators (store, city, pin_code, address, landmark, opening_time, closing_time, phone_number, website_url, map_url, page_no) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        cur.execute(query, (data), )
        conn.commit()


def scrap(start_page_no, end_page_no):
    for page_no in range(start_page_no, end_page_no + 1):
        query = f'select * from page_data where page_no={page_no}'
        cur.execute(query)
        data = cur.fetchall()

        if data:
            print(f"This Page with page number {page_no} is already scraped..")
            page_no += 1
            continue

        res = requests.get(f"https://stores.burgerking.in/?page={page_no}", cookies=cookies, headers=headers)
        content = html.fromstring(res.content)
        containers = content.xpath('//div[@class="store-info-box"]')

        for container in containers:
            opening_time = 'NA'
            closing_time = 'NA'
            store = container.xpath('./ul/li[@class="outlet-name"]/div[@class="info-text"]/a/text()')[0].strip(' ')
            phone = container.xpath('./ul/li[@class="outlet-phone"]/div[@class="info-text"]/a/text()')[0].replace(' ',
                                                                                                                  '')
            if '+91' not in phone:
                phone = f"+91{phone}"
            map_link = container.xpath('./ul/li[@class="outlet-actions"]/a[@class="btn btn-map"]/@href')[0]
            web_link = container.xpath('./ul/li[@class="outlet-actions"]/a[@class="btn btn-website"]/@href')[0]

            address_lines = container.xpath('./ul/li[@class="outlet-address"]/div[@class="info-text"]//span/text()')

            landmark = container.xpath('./ul/li[not(@class)]/div[@class="info-text"]/text()')
            if landmark:
                landmark = landmark[0].strip(' ')
            else:
                landmark = 'NA'
            address = f"{address_lines[0]} {address_lines[1]}"
            city = address_lines[2]
            pincode = address_lines[4]

            timing = container.xpath('./ul/li[@class="outlet-timings"]/div[@class="info-text"]/span/text()')[0]

            if "Open until" in timing:
                closing_time = timing.replace("Open until ", '')
            elif "Opens from" in timing:
                time = timing.split('to')
                opening_time = time[0].replace("Opens from", '').strip(' ')
                closing_time = time[1].lstrip(' ')
            elif "Open 24 Hours" in timing:
                opening_time = "00:00"
                closing_time = "24:00"
            else:
                time = timing.split('-')
                opening_time = time[0].strip(' ')
                closing_time = time[1].lstrip(' ')

            data = (
                store, city, pincode, address, landmark, opening_time, closing_time, phone, web_link, map_link, page_no)
            db_store(data)
        db_store((page_no, 'SUCCESS', len(containers)), 'SUCCESS')


if __name__ == '__main__':
    scrap(int(sys.argv[1]), int(sys.argv[2]))
