import boto3
import scrapy
import os
import csv
from scrapy.crawler import CrawlerProcess
import locale

s3 = boto3.client('s3')

BUCKET = 'covid-tracker-801101744'
KEY = 'handle-csv/covid-global.csv'

locale.setlocale(locale.LC_ALL, '')


def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class ScaperCovid(scrapy.Spider):
    name = 'scrape_all'
    start_urls = [
        'https://www.worldometers.info/coronavirus/'
    ]

    data_list = {}

    def parse(self, response, d_list=data_list):
        rows = response.xpath('//table/tbody[1]/tr[not(@class)]')
        # print('@-@-@-' * 100, rows[0].extract())

        for row in rows[1:]:

            new_cases = 0
            get_second_element = row.css('td')[2].extract().split('</td>')[0].strip()
            if represents_int(get_second_element[-1:]):
                new_cases = (get_second_element.split(
                    '<td style="font-weight: bold; text-align:right;background-color:#FFEEAA;">+')[1].replace(",", "").strip())

            deaths = 0
            get_third_element = row.css('td')[3].extract().split('</td>')[0].strip()
            if represents_int(get_third_element[-1:]):
                deaths = (get_third_element.split('<td style="font-weight: bold; text-align:right;">')[1].replace(",", "").strip())

            new_deaths = 0
            get_fourth_element = row.css('td')[4].extract().split('</td>')[0].strip()
            if represents_int(get_fourth_element[-1:]):
                new_deaths = (
                    get_fourth_element.split('text-align:right;background-color:red; color:white">+')[1].replace(",", "").strip())

            recovered = 0
            get_fifth_element = row.css('td')[5].extract().split('</td>')[0].strip()
            if represents_int(get_fifth_element[-1:]):
                recovered = (get_fifth_element.split('<td style="font-weight: bold; text-align:right">')[1].replace(",", "").strip())

            place_name = row.css('td a::text').extract_first()
            if place_name == "USA":
                place_name = "United States"
            if place_name == "S. Korea":
                place_name = "South Korea"
            if place_name == "Bosnia and Herzegovina":
                place_name = "Bosnia"
            if place_name == "UAE":
                place_name = "United Arab Emirates"
            if place_name == "Czechia":
                place_name = "Czech Republic"
            if place_name == "UK":
                place_name = "United Kingdom"
            if place_name == "UK":
                place_name = "United Kingdom"
            if place_name == "CAR":
                place_name = "Central African Republic"

            d_list[place_name] = {
                'cases': int(row.css('td::text')[0].extract().replace(",", "").strip()) - int(new_cases),
                'new_cases': int(new_cases),
                'total_cases': int(row.css('td::text')[0].extract().replace(",", "").strip()),
                'deaths': int(deaths) - int(new_deaths),
                'new_deaths': int(new_deaths),
                'total_deaths': int(deaths),
                'recovered': int(recovered),
                'region': 'global'
            }

        yield response.follow('https://docs.google.com/spreadsheets/d/e/2PACX-1vR30F8lYP3jG7YOq8es0PBpJIE5yvRVZffOyaqC0GgMBN6yt0Q-NI8pxS7hd1F9dYXnowSC6zpZmW9D/pubhtml?gid=0&amp;single=true&amp;widget=true&amp;headers=false&amp;range=A1:I208#', callback=self.parse_bno_news)

   
    def parse_bno_news(self, response, d_list=data_list):

        rows = response.css('div#0 table tbody tr')
        rows = rows[7:-3]

        for row in rows:
            country_name = row.css('td::text')[0].extract()

            cases = 0
            if row.css('td::text')[1].extract() != 'N/A':
                cases = int(row.css('td::text')[1].extract().replace(",", ""))

            new_cases = 0
            if row.css('td::text')[2].extract() != 'N/A':
                new_cases = int(row.css('td::text')[2].extract().replace(",", ""))

            total_cases_bno = cases + new_cases

            deaths = 0
            if row.css('td::text')[3].extract() != 'N/A':
                deaths = int(row.css('td::text')[3].extract().replace(",", ""))

            new_deaths = 0
            if row.css('td::text')[4].extract() != 'N/A':
                new_deaths = int(row.css('td::text')[4].extract().replace(",", ""))

            recovered = 0
            print(country_name, row.css('td::text')[7])
            if row.css('td::text')[7].extract() != 'N/A':
                if ',' in row.css('td::text')[7].extract():
                    recovered = int(row.css('td::text')[7].extract().replace(",", ""))
                elif '.' in row.css('td::text')[7].extract():
                    recovered = int(row.css('td::text')[7].extract().replace(".", ""))

            region = 'global'

            if country_name == "Congo":
                country_name = "DR Congo"

            if country_name in d_list:
                total_cases_wm = d_list.get(country_name).get('total_cases')
                if total_cases_bno > total_cases_wm:
                    d_list[country_name] = {
                        'cases': cases,
                        'new_cases': new_cases,
                        'total_cases': total_cases_bno,
                        'deaths': deaths,
                        'new_deaths': new_deaths,
                        'total_deaths': deaths + new_deaths,
                        'recovered': recovered,
                        'region': region
                    }

        d_list["Total"] = {
            'cases': sum(int(i.get("cases")) for i in d_list.values()),
            'new_cases': sum(int(i.get("new_cases")) for i in d_list.values()),
            'total_cases': sum(int(i.get("total_cases")) for i in d_list.values()),
            'deaths': sum(int(i.get("deaths")) for i in d_list.values()),
            'new_deaths': sum(int(i.get("new_deaths")) for i in d_list.values()),
            'total_deaths': sum(int(i.get("total_deaths")) for i in d_list.values()),
            'recovered': sum(int(i.get("recovered")) for i in d_list.values()),
            'region': 'global'
        }

        for k, v in d_list.items():
            yield {
                "place": k,
                "cases": v.get("cases"),
                # "cases_comma": f'{v.get("cases"):n}',
                "new_cases": v.get("new_cases"),
                # "new_cases_comma": f'{v.get("new_cases"):n}',
                "total_cases": v.get("total_cases"),
                # "total_cases_comma": f'{v.get("total_cases"):n}',
                "deaths": v.get("deaths"),
                # "deaths_comma": f'{v.get("deaths"):n}',
                "new_deaths": v.get("new_deaths"),
                # "new_deaths_comma": f'{v.get("new_deaths"):n}',
                "total_deaths": v.get("total_deaths"),
                # "total_deaths_comma": f'{v.get("total_deaths"):n}',
                "recovered": v.get("recovered"),
                # "recovered_comma": f'{v.get("recovered"):n}',
                "region": v.get("region")
            }


def main(event, context):

    # ---------------------------S3-----------------------------

    # data = open(KEY, 'rb')
    res = s3.list_objects_v2(Bucket=BUCKET, Prefix=KEY, MaxKeys=1)
    if 'Contents' in res:
        print(res)
        s3.delete_object(Bucket=BUCKET, Key=KEY)
    # s3.put_object(Bucket=BUCKET, Key=KEY, Body=data)

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'FEED_FORMAT': 'csv',
        'FEED_URI': 's3://'+BUCKET+'/'+KEY
    })

    process.crawl(ScaperCovid)
    process.start()

    print('All done !')


if __name__ == "__main__":
    main('', '')
