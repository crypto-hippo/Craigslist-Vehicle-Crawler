import requests
import re
import time 
from bs4 import BeautifulSoup


class CraigslistCrawler(object):
    
    def __init__(self):
        self.vehicle_ads_start_link = "https://asheville.craigslist.org/search/cta?s=%s"
        self.all_links = set([])
        self.timer = 1
        self.parser = None 
        self.pagination = 0
        self.pagination_increment = 120
        self.pagination_limit = 0 
        self.pagination_total_count_regexp = re.compile('<span class="totalcount">(.*?)</span>')
        self.cars = [] 


    # fetch all links recursively
    def fetch_all_links(self):
        start_link = self.vehicle_ads_start_link % self.pagination
        first_page = requests.get(start_link).content
        self.pagination_limit = self.get_pagination_totalcount(first_page)
        self.crawl(first_page)
        print "Found %s links" % len(self.all_links)
        
    
    # accepts html string, returns array of all ad links on that page
    def fetch_links(self, page_content):
        self.parser = BeautifulSoup(page_content, 'html.parser')
        return self.parser.find_all('a', class_="result-image")

    def crawl(self, page_content):
        time.sleep(2)
        ads = self.fetch_links(page_content)
        links = set(map(lambda ad: ad["href"], ads))
        for link in links:
            self.cars.append(self.create_car_object(link))
            
        self.all_links = self.all_links | links

        if self.pagination + 120 > self.pagination_limit:
            return self.all_links 

        else:
            self.pagination += 120
            next_link = self.vehicle_ads_start_link % self.pagination
            next_page_content = requests.get(next_link).content 
            return self.crawl(next_page_content)


    def create_car_object(self, link):
        time.sleep(2)
        print "Creating car object from unique link: %s" % link 
        content = requests.get(link).content 
        parser = BeautifulSoup(content, 'html.parser')
        title = self.get_title(parser)
        

    def get_title(self, parser):
        title_only_tag = parser.find("span", {"id": "titletextonly"})
        return str(title_only_tag.getText().encode("utf-8")).lower() if title_only_tag != None else None

    def get_price(self, parser):
        price_tag = parser.find("span", {"class": "price"})
        return str(price_tag.getText().encode("utf-8")).split("$")[1] if price_tag != None else None

    def get_image_links(self):
        img_thumbs_container = self.html_parser.find("div", {"id":"thumbs"})
        if img_thumbs_container is None:
            return None 

        images = img_thumbs_container.find_all("a", {"class":"thumb"})
        return ",".join([ str(link["href"]) for link in images ])

    def get_pagination_totalcount(self, html):
        try:
            match = self.pagination_total_count_regexp.search(html)
            return match.groups(0)[0] if match else self.pagination

        except Exception as e:
            return self.pagination


crawler = CraigslistCrawler()
crawler.fetch_all_links()


        

    
