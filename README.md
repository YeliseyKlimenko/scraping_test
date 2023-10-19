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
3. Run the spider by running
```
scrapy crawl yelp_spider -a category="<category>" -a location="<location>"
```
For example:
```
scrapy crawl yelp_spider -a category="Contractors" -a location="Texas City, TX"
```
4. The results will be saved in a json file in the results folder in project root directory.