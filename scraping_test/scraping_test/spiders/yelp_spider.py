import scrapy
import scrapy.cmdline
import re
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
    print(url)

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


def get_business_website_link(element: Selector) -> str:
    if element and "biz_redir" in element.get():
        decoded_url = unquote(element.get())
        params = parse_qs(urlparse(decoded_url).query)
        return params.get('url')[0]


class YelpSpider(scrapy.Spider):
    name = "yelp_spider"

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
        print("Parsing website...")
        business_details_container = response.xpath(
            "//div[re:test(@class, 'biz-details-page-container-inner__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]").xpath(
            ".//div[contains(@data-testid, 'sidebar-content')]")

        business_website_url = ""
        if business_details_container:
            contacts = business_details_container[0].xpath(".//section/div/child::div")
            if contacts:
                for contact in contacts:
                    url = contact.xpath(".//a/@href")
                    business_website_url = get_business_website_link(url)
        #
        # reviews_element = response.xpath("//div[contains(@id, 'reviews')]").xpath(
        #     ".//ul[re:test(@class, 'undefined list__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/child::li")
        #
        # reviews = []
        # for review in reviews_element:
        #     while len(reviews) < 5:
        #         review_attributes = review.xpath(
        #             ".//div/child::div")
        #
        #         reviewer_name = review_attributes[0].xpath('string()').get().split('\n')[1]
        #         review_location = review_attributes[0].xpath('string()').get().split('\n')[2]
        #
        #         date_format = "%b %d, %Y"
        #
        #         review_date = datetime.strptime(review_attributes[1].xpath('.//div/div[2]').get(), date_format)
        #
        #         reviews.append({
        #             'reviewer_name': reviewer_name,
        #             'review_location': review_location,
        #             'review_date': review_date
        #         })
        #
        reviews = []
        # business_website_url = ""
        data = response.request.meta['business_data']
        print({**data,
               'business_website_url': business_website_url,
               'reviews': reviews})
        yield {
            **data,
               'business_website_url': business_website_url,
               'reviews': reviews
                }

    def parse(self, response):
        business_list = response.xpath(
            "//ul[re:test(@class, 'undefined list__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/child::li")
        for business in business_list:
            main_attributes = business.xpath(
                ".//div[re:test(@class, 'mainAttributes__[a-zA-Z0-9]{5}__[a-zA-Z0-9]{5}')]/div/child::div")

            if main_attributes:
                business_data = {
                    'name': main_attributes[0].xpath('string()').get(),
                    'rating': main_attributes[1].xpath('string()').get().split(' ')[0],
                    'review_count': re.findall(r'-?\d+', main_attributes[1].xpath('string()').get().split(' ')[1])[0],
                    'business_yelp_url': get_yelp_business_link(business),
                }

                yield scrapy.Request(url=get_yelp_business_link(business),
                                     callback=self.parse_website,
                                     meta={'business_data': business_data}
                                     )
