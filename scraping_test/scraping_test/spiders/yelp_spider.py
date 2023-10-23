import scrapy
import scrapy.cmdline
import re
import json
from urllib.parse import urlparse, urlunparse, unquote, parse_qs, ParseResult
from datetime import datetime

from scrapy import Selector


def get_yelp_business_link(element: Selector):
    business_links = element.xpath(".//a/@href").getall()
    url = ""
    for link in business_links:
        if "/biz/" in link:
            url = link
            break

    parsed_url = urlparse(url)

    cleaned_url = ParseResult(
        scheme=parsed_url.scheme,
        netloc=parsed_url.netloc,
        path=parsed_url.path,
        params=parsed_url.params,
        query="",
        fragment=parsed_url.fragment
    )

    cleaned_url = urlunparse(cleaned_url)

    return 'https://www.yelp.com' + cleaned_url


def get_business_website_link(url: str) -> str:
    decoded_url = unquote(url)
    params = parse_qs(urlparse(decoded_url).query)
    return params.get('url')[0]


class YelpSpider(scrapy.Spider):
    name = "yelp_spider"
    alt_output_location = '../../results/alt_output.json'

    def __init__(self, *args, **kwargs):
        super(YelpSpider, self).__init__(*args, **kwargs)
        self.category = kwargs.get('category')
        self.location = kwargs.get('location')

    def start_requests(self):
        if not self.category or not self.location:
            self.logger.error("You must specify 'category' and 'location' as arguments.")
            return

        url = f'https://www.yelp.com/search?find_desc={self.category}&find_loc={self.location}'
        yield scrapy.Request(url, callback=self.parse)

    def parse_website(self, response):
        business_details_container = response.xpath(
            "//div[re:test(@class, 'biz-details-page-container-inner__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]").xpath(
            ".//div[contains(@data-testid, 'sidebar-content')]")

        business_website_url = ""
        if business_details_container:
            urls = business_details_container[0].xpath(".//a/@href")
            if urls:
                for url in urls:
                    if "biz_redir" in url.get():
                        business_website_url = get_business_website_link(url.get())
                        break

        reviews_element = response.xpath("//div[contains(@id, 'reviews')]").xpath(
            ".//ul[re:test(@class, 'undefined list__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/child::li")

        reviews = []
        for review in reviews_element:
            if len(reviews) < min(5, int(response.request.meta['business_data']['review_count'])):
                review_attributes = review.xpath(".//child::*")

                user_passport_info = review_attributes[0].xpath(
                    ".//div[re:test(@class, 'user-passport-info')]/child::*")

                reviewer_name = user_passport_info[0].xpath('string()').get()
                review_location = user_passport_info[1].xpath('string()').get()

                input_date_format = "%b %d, %Y"
                output_date_format = "%Y-%m-%d"
                pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2},\s\d{4}\b'

                attr_text = [attr.xpath("string()").get() for attr in review_attributes]
                matches = [re.findall(pattern, s) for s in attr_text]
                matches = [match for match in matches if match]

                review_date = datetime.strftime(datetime.strptime(matches[0][0],
                                                                  input_date_format),
                                                output_date_format)

                reviews.append({
                    'reviewer_name': reviewer_name,
                    'review_location': review_location,
                    'review_date': review_date
                })

        data = response.request.meta['business_data']
        full_data = {**data,
                     'business_website_url': business_website_url,
                     'reviews': reviews}
        print(full_data)
        yield full_data

    def parse(self, response):
        business_list = response.xpath(
            "//ul[re:test(@class, 'undefined list__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/child::li")
        data_list = []
        url_list = []
        for business in business_list:
            main_attributes = business.xpath(
                ".//div[re:test(@class, 'mainAttributes__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/div/child::div")

            if main_attributes:
                review_count = 0
                try:
                    review_count = int(
                        re.findall(r'-?\d+', main_attributes[1].xpath('string()').get().split(' ')[1])[0])
                except Exception:
                    pass

                business_data = {
                    'name': main_attributes[0].xpath('string()').get(),
                    'rating': main_attributes[1].xpath('string()').get().split(' ')[0],
                    'review_count': review_count,
                    'business_yelp_url': get_yelp_business_link(business),
                }

                data_list.append(business_data)
                url_list.append(get_yelp_business_link(business))

        for data, url in zip(data_list, url_list):
            yield scrapy.Request(url=url,
                                 callback=self.parse_website,
                                 meta={'business_data': data}
                                 )
