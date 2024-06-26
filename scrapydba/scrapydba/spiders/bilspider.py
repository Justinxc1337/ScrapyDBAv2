import csv
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.signalmanager import dispatcher
import sqlite3


#Test spider for DBA Biler, (kan nemt ændres til anden hjemmeside eller produkt)
#Test Bil Peugeot 108 (A.R)
#https://www.dba.dk/biler/biler/maerke-peugeot/modelpeugeot-108/
#Database completely fucked if run again with same name

class BilspiderSpider(scrapy.Spider):
    name = "bilspider"
    start_urls = ['https://www.dba.dk/biler/biler/maerke-peugeot/modelpeugeot-108/']

    def __init__(self):
        super(BilspiderSpider, self).__init__()

        self.conn = sqlite3.connect('bildb.db')
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                model TEXT,
                pris TEXT,
                farve TEXT,
                brændstof TEXT,
                modelår TEXT,
                kilometer TEXT,
                service TEXT,
                UNIQUE(model, pris, farve, brændstof, modelår, kilometer, service)
            )
        ''')

    def parse(self, response):
        bil_link = response.css('.listingLink::attr(href)').extract()
        for link in bil_link:
            yield response.follow(link, callback=self.parse_car)

    def parse_car(self, response):
        data = {}
        dl_elements = response.css('.vip-matrix-data dl dt')
        for dt_element in dl_elements:
            key = dt_element.css('::text').get().strip()
            value = dt_element.xpath('following-sibling::dd[1]/text()').get().strip()
            data[key] = value

        model = data.get('Mærke og model')
        pris = response.css('.price-tag::text').get().strip()
        farve = data.get('Farve')
        brændstof = data.get('Brændstof')
        modelår = data.get('Modelår')
        kilometer = data.get('Antal km')
        service = data.get('Service')

        yield {
            'model': model,
            'pris': pris,
            'farve': farve,
            'brændstof': brændstof,
            'modelår': modelår,
            'kilometer': kilometer,
            'service': service
        }
        
        self.c.execute('''
            INSERT OR IGNORE INTO cars (model, pris, farve, brændstof, modelår, kilometer, service)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (model, pris, farve, brændstof, modelår, kilometer, service))
        self.conn.commit()
            
    def closed(self, reason):
        self.conn.close()
        
        #next_page_link = response.css('.trackClicks.pagination-modern-next.a-page-link::attr(href)').get()
        #if next_page_link:
            #yield response.follow(next_page_link, callback=self.response_parser)
            
def bil_spider_result():
    biler_results = []

    def crawler_results(item):
        biler_results.append(item)

    dispatcher.connect(crawler_results, signal=signals.item_scraped)
    crawler_process = CrawlerProcess()
    crawler_process.crawl(BilspiderSpider)
    crawler_process.start()
    return biler_results


if __name__ == '__main__':
    bil_data=bil_spider_result()

    #keys = bil_data[0].keys()
    #with open('bil_data.csv', 'w', newline='', encoding='utf-8') as output_file_name:
        #writer = csv.DictWriter(output_file_name, keys)
        #writer.writeheader()
        #writer.writerows(bil_data)