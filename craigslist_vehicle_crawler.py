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
        print "\nCreating car object from unique link: \n%s" % link 
        content = requests.get(link).content 
        parser = BeautifulSoup(content, 'html.parser')
        title = self.get_title(parser)
        price = self.get_price(parser)
        image_links = self.get_image_links(parser)
        city = self.get_city(link)
        attr_groups = self.organize_attr_group_data(parser)

        print "\nShowing car data\n"
        print "Title: %s" % title 
        print "Price: %s" % price 
        print "Images: %s" % image_links

        print "City: %s" % city 
        for key in attr_groups:
            print "%s: %s" % (key.capitalize(), attr_groups[key] )

    def get_title(self, parser):
        title_only_tag = parser.find("span", {"id": "titletextonly"})
        return str(title_only_tag.getText().encode("utf-8")).lower() if title_only_tag != None else None

    def get_price(self, parser):
        price_tag = parser.find("span", {"class": "price"})
        return str(price_tag.getText().encode("utf-8")).split("$")[1] if price_tag != None else None

    def get_image_links(self, parser):
        img_thumbs_container = parser.find("div", {"id":"thumbs"})
        if img_thumbs_container is None:
            return None 

        images = img_thumbs_container.find_all("a", {"class":"thumb"})
        return ",".join([ str(link["href"]) for link in images ])

    def get_city(self, url):
        city_from_url = url.split("//")[1].split(".")[0]
        return city_from_url.lower()

    def is_valid_year(self, string):
        try:
            year = int(string[:4])
            return True

        except Exception as e:
            return False

    def get_year_make_model(self, subtitle):
        args = subtitle.split(" ")
        year, make, model = None, None, None
        if len(args) > 2:
            year = args[0]
            make = args[1].lower()
            model = args[2].lower()
        elif len(args) == 2:
            year = args[0]
            make = args[1].lower()
        elif len(args) == 1:
            pass

        return year, make, model

    def organize_attr_group_data(self, parser):
        current_attr_groups = {}
        try:
            attr_groups = parser.find_all("p", {"class": "attrgroup"})
            for ptag in attr_groups:
                span_tags = ptag.find_all("span")

                for stag in span_tags:
                    inner_string = str(stag.getText().encode("utf-8")).lower()
                    inner_string_args = inner_string.split(": ")

                    if len(inner_string_args) == 1 and self.is_valid_year(inner_string):
                        year, make, model = self.get_year_make_model(inner_string)

                        subtitle = inner_string
                        current_attr_groups["year"] = year 
                        current_attr_groups["make"] = make
                        current_attr_groups["model"] = model
                        current_attr_groups["subtitle"] = subtitle

                    elif len(inner_string_args) == 2:

                        data_label, data_value = inner_string_args
                        # print data_label, data_value

                        if data_label == "condition":
                            current_attr_groups["vehicle_condition"] = data_value.lower()

                        elif data_label == "fuel":
                            current_attr_groups["fuel"] = data_value.lower()

                        elif data_label == "odometer":
                            current_attr_groups["odometer"] = data_value

                        elif data_label == "paint color":
                            current_attr_groups["paint_color"] = data_value.lower()

                        elif data_label == "vin":
                            current_attr_groups["vin"] = data_value.lower()

                        elif data_label == "cylinders":
                            current_attr_groups["cylinders"] = ''.join([ letter for letter in data_value if letter.isdigit() ])

                        elif data_label == "transmission":
                            current_attr_groups["transmission"] = data_value.lower()

                        elif data_label == "title status":
                            current_attr_groups["title_status"] = data_value.lower()

                        elif data_label == "type":
                            current_attr_groups["type"] = data_value.lower()

                        elif data_label == "size":
                            current_attr_groups["size"] = data_value.lower()

                        elif data_label == "drive":
                            current_attr_groups["drive"] = data_value.lower()

                        else:
                            pass
                            # print "[+] craigslist ad label condition not being tested for. html_parser 125"
                            # print (data_label, data_value)
            return current_attr_groups
        except Exception as e:
            print str(e)
        
        finally:
            return current_attr_groups

    def get_pagination_totalcount(self, html):
        try:
            match = self.pagination_total_count_regexp.search(html)
            return match.groups(0)[0] if match else self.pagination

        except Exception as e:
            return self.pagination


crawler = CraigslistCrawler()
crawler.fetch_all_links()


        

    
