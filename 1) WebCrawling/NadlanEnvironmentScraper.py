"""
The following class and code has been written by
Maor Bezalel and Nadav Bitran Noma.

__Brief Summary__:
The class serves as a secondary scraper to the already NadlanScraper.
In this class, we don't scrape data regarding housing units,
but more general information, which delves into environmental
data related to the neighborhoods of the housing units 
we scraped in our main scraper.

In terms of the environmental data itself, there are 3 types of data we collect:

    1.  Data related to the number of schools, kindergartens and 
        educational institutions in the neighborhoods, as well as 
        the average distance from them within each neighborhood.

    2.  Data related to the amount of open green areas and 
        public parks and gardens in the neighborhoods and, in addition, 
        the average distance from them within each neighborhood.

    3. Data related to the amount of public buildings, such as:
        A. public institutions (practitioners, clinics, asylums, courts, etc.);
        B. community institutions (shopping centers, shopping malls, markets, shops, offices, banks, etc.);
        C. Religious institutions (synagogues, churches and mosques).
"""


import pandas as pd
import numpy as np
import sys
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import time

class NadlanEnvironmentScraper(object):
    def __init__(self) -> None:
        # Where we store neighbourhoods' environmental data, 
        # before converting it into a Pandas DataFrame
        self.environment_dict = self.create_data_dict_keys()
        
        # Following lists contain the names of the keys of our dictionary
        # based on the category the belong to
        self.education_keys_list = ["Schools", "Kindergartens_And_Dormitories", "Non_Formal_Educational_Institutions", "Education_Average_Distance"]
        self.green_areas_keys_list = ["Green_Areas_SQM", "Parks_And_Gardens", "Green_Areas_Average_Distance", "Parks_And_Gardens_Average_Distance"]
        self.public_buildings_keys_list = ["Public_Institutions", "Community_Institutions", "Religious_Institutions", "Public_Building_Average_Distance"]

        # Our main Neighbourhoods' environmental data container.
        self.environment_df = pd.DataFrame(data=self.environment_dict)
        
        # How many cities are we going to scrape data from.
        # NOTE: Be advised, this is a CONSTANT variable!
        self.NUM_OF_CITIES: int = 80

        # Where we contain our web scraping driver
        self.environment_driver = self.create_environment_driver()

        # action chain object creation -> will help us click some complicated buttons
        self.action = ActionChains(self.environment_driver)
    
    # Create the WebDriver and set it on the scraping target url
    def create_environment_driver(self) -> WebDriver:
        crawling_target_url = "https://www.nadlan.gov.il/Pricing"
        environment_driver = webdriver.Chrome()
        environment_driver.maximize_window()
        environment_driver.get(crawling_target_url)
        return environment_driver

    def create_data_dict_keys(self) -> dict[str, list]:
        return {
            "City": [],
            "Neighborhood": [],
            "Schools": [],
            "Kindergartens_And_Dormitories": [],
            "Non_Formal_Educational_Institutions": [],
            "Education_Average_Distance": [],
            "Green_Areas_SQM": [],
            "Parks_And_Gardens": [],
            "Green_Areas_Average_Distance": [],
            "Parks_And_Gardens_Average_Distance": [],
            "Public_Institutions": [],
            "Community_Institutions": [],
            "Religious_Institutions": [],
            "Public_Building_Average_Distance": [],
        }

    # Reset the data from our environment dictionary
    def reset_dict_data(self) -> None:
        self.environment_dict = {key: [] for key in self.environment_dict.keys()}

    # This is where combine and perform our three main scraping operations:
    # 1. City Scraper --> To gain a scraping accesses to the neighborhoods in each city
    # 2. Neighborhood Scraper --> To gain a scraping accesses to the housing units in each Neighborhood
    # 3. Environmental Data Scraper --> Where we collect the data!
    def main_scrapper(self) -> None:
        # Iterate through each city
        for city_num in range(self.NUM_OF_CITIES):
            self.display_neighborhood_table()
             # Enter the current city page and get its name
            city_name = self.scrape_city(idx=city_num)
            # Iterate through each neighborhood in the city
            for neighborhood_num in range(self.get_number_of_neighborhoods()):
                # Enter the current neighborhood page
                neighborhood_name = self.scrape_neighborhood(idx=neighborhood_num)
                 # If there are no more neighborhood in the city, break out of the loop
                if neighborhood_name is None: break
                # Collect all the environmental data in the current neighborhood
                self.scrape_environmental_data(city_name, neighborhood_name)
                # Store the collected data to a CSV file
                self.store_the_dict_in_the_df()
                self.environment_df.to_csv("AllCitiesEnvironment5.csv", index=False)
                self.reset_dict_data()
                # Go back to the current city's neighborhoods page
                self.exit_to_the_previous_page()
                self.display_neighborhood_table()
            # Go back to the cities page
            self.exit_to_the_previous_page()
        # Store any remaining data & Write the final data to a CSV file
        self.store_the_dict_in_the_df()
        self.environment_df.to_csv("AllCitiesEnvironment5.csv", index=False)

    # This method navigates to the specified city after clicking on the corresponding button.
    # After getting the button element for the city's neighborhoods page.
    def scrape_city(self, idx: int) -> str:
        # Find all the city buttons presented in the current page
        # (we do it because everytime a new page is loaded, the previous elements become stale)
        try:
            time.sleep(2)
            # button.text -> means that we are searching for elements with a tag name of button who stands in the 'text' css class
            cities_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'button.text')))
        except:
            cities_buttons_list = [] # ignore
            raise Exception("Failure in 'scrape_city' method!")
        city_name = cities_buttons_list[idx].text[8::]
        self.enter_page(cities_buttons_list[idx])
        return city_name

    # This method navigates to the specified neighborhood after clicking on the corresponding button.
    # If the button is empty (indicating there are no more neighborhoods), it returns None.
    # Otherwise, it scrolls to the bottom of the page and returns a list of rows that contains the data
    # of the housing units on the neighborhood.
    def scrape_neighborhood(self, idx: int) -> None | str:
        try:
            time.sleep(2)
            # button.text -> means that we are searching for elements with a tag name of button who stands in the 'text' css class
            neighborhoods_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'button.text')))
        except:
            neighborhoods_buttons_list = [] # ignore
            print("Failure in 'scrape_neighborhood' method!")
            self.close_environment_driver()
        neighborhood_name = neighborhoods_buttons_list[idx].text
        if idx == 0:
            # This condition is necessary for extracting the first neighborhood name of Herzliya because of the way the website is programmed
            neighborhood_name = neighborhood_name[6::]
            if neighborhood_name == '': 
                neighborhood_name ="מרכז מזרחי"   
        # If there are no more neighborhoods, return None
        if self.is_button_empty(neighborhood_name):
            return None
        # Go to the neighborhood page and wait for it to reload
        self.enter_page(neighborhoods_buttons_list[idx])
        # Return the name of the neighborhood
        return neighborhood_name

    # This method iterate through each valid environmental information in the current neighborhood
    # and gain acessess to its data in-order to store it in our dictionary
    def scrape_environmental_data(self, city_name: str, neighborhood_name: str) -> None:
        try:
            # We click on the "מה בסביבה" button to gain acessess to the
            # environmental information of the current neighborhood
            time.sleep(2)
            environmental_info_button = self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR,'a.mwa-top-bar__mwa')))
            self.action.click(environmental_info_button).perform()
            #self.action.double_click(environmental_info_button).perform()
            # The data is inside an inner HTML, which is inside another iframe.
            # We just tell the driver to focus on the desired iframe
            iframe = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'iframe')))[1]
            self.environment_driver.switch_to.frame(iframe)
            self.collect_environmental_data(city_name, neighborhood_name)
        except:
            raise Exception("Failure in 'scrape_environmental_data' method!") 

    # For each valid valid environmental information we collect its data
    def collect_environmental_data(self, city_name: str, neighborhood_name: str) -> None:
        time.sleep(10)
        try:
            self.environment_dict["City"].append(city_name)
            self.environment_dict["Neighborhood"].append(neighborhood_name)
            self.collect_education_related_data()
            public_buildings_and_green_areas_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'b.ng-binding')))
            self.collect_green_areas_related_data(public_buildings_and_green_areas_list[5:9])
            self.collect_public_buildings_related_data(public_buildings_and_green_areas_list[9:])
        except:
            raise Exception("Failure in 'collect_environmental_data' method!")
            
    def collect_education_related_data(self) -> None:
        data_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.mwa-education__item-title.ng-binding')))
        for data, key in list(zip(data_list, self.education_keys_list)):
            self.environment_dict[key].append(data.text)

    def collect_green_areas_related_data(self, data_list: list[WebElement]) -> None:
        for data, key in list(zip(data_list, self.green_areas_keys_list)):
            self.environment_dict[key].append(data.text)
    
    def collect_public_buildings_related_data(self, data_list: list[WebElement]) -> None:
        data_list.append(self.wait().until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.mwa-cols__item-title.ng-binding'))))
        for data, key in list(zip(data_list, self.public_buildings_keys_list)):
            self.environment_dict[key].append(data.text)
        
    # For the page to contain table data of neighborhoods and not streets
    def display_neighborhood_table(self) -> None:
        time.sleep(2)
        try:
            neighborhoods_button = self.wait().until(EC.presence_of_all_elements_located((By.TAG_NAME,"button")))[10]
            neighborhoods_button.click()
        except:
            raise Exception("Failure in 'display_neighborhood_table' method!")

    def get_number_of_neighborhoods(self) -> int:
        try:
            time.sleep(2)
            neighborhoods_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"button.text")))
        except:
            neighborhoods_buttons_list = [] # ignore
            raise Exception("Failure in 'get_number_of_neighborhoods' method!")
        finally:
            return len(neighborhoods_buttons_list)

    # Check if the text in a given button element is empty
    def is_button_empty(self, button_text: str) -> bool:
        # Return True if the first character of the button's text is a space
        return button_text[0] == " "

    def wait(self) -> WebDriverWait:
        # Creating WebDriverWait object that sets poll freq of every 1sec with a 60sec wait until timeout
        return WebDriverWait(self.environment_driver, timeout=5, poll_frequency=1.0)    

    # Click on a given button element and wait for it to reload
    def enter_page(self, button: WebElement) -> None:
        button.click()

    # Go back to the previous page and wait for it to reload
    def exit_to_the_previous_page(self) -> None:
        self.environment_driver.back()
        self.environment_driver.refresh()

    # Store the contents of the nadlan_dict dictionary in the environment_df dataframe
    def store_the_dict_in_the_df(self) -> None:
        self.environment_df = self.environment_df.append(pd.DataFrame.from_dict(self.environment_dict))

    # Where we close the web driver and end the crawling
    def close_environment_driver(self) -> None:
        self.environment_driver.close()
        print("Finished Crawling!")
