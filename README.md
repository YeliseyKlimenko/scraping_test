# Yelp Scraper

## Description
This is a scrapy spider that scrapes the yelp website for business information and reviews.

## Installation
1. Clone this repository
2. Install the requirements by running
```
poetry shell
poetry install
```
3. Navigate to the python package directory
```
cd scraping_test/scraping_test
```
4. Activate the spider by running
```
scrapy crawl yelp_spider -a category="<category>" -a location="<location>"
```
For example:
```
scrapy crawl yelp_spider -a category="Contractors" -a location="Texas City, TX"
```
5. The results will be saved in a json file in the results folder in project root directory.

Note: To scrape yelp.com, you have to disobey robots.txt. This results in the site blocking access from your network (returns 503 status code). That can interfere with the scraping process.