"""
The following class and code has been written by
Maor Bezalel and Nadav Bitran Noma.

__Brief Summary__:
The class is a web scraper for the website "https://www.nadlan.gov.il/Pricing".
It is written in Python and uses the selenium and pandas libraries.
It opens a Chrome web browser and navigates to the specified URL.
It then locates elements on the page using their class name and tag name,
and interacts with them by clicking on them.
It scrolls down the page to load more data, collects the data from the page,
and stores it in a dictionary.
Finally, it converts the dictionary to a CSV file and saves it to disk
everytime the dictionary as reached 1 MB and also once again
at the end of the code.
"""

import pandas as pd
import numpy as np
import sys
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import time

class NadlanScraper(object):
    def __init__(self) -> None:
        # Where we store housing units data, before converting it
        # into a Pandas DataFrame
        self.nadlan_dict = self.create_data_dict_keys()

        # Our main Nadlan data container.
        self.nadlan_df = pd.DataFrame(data=self.nadlan_dict)

        # How many cities are we going to scrape data from.
        # NOTE: Be advised, this is a CONSTANT variable!
        self.NUM_OF_CITIES: int = 80

        # Where we contain our web crawling driver
        self.nadlan_driver = self.create_nadlan_driver()


    # Create the WebDriver and set it on the scraping target url
    def create_nadlan_driver(self) -> WebDriver:
        crawling_target_url = "https://www.nadlan.gov.il/Pricing"
        nadlan_driver = webdriver.Chrome()
        nadlan_driver.get(crawling_target_url)
        return nadlan_driver

    def wait(self) -> WebDriverWait:
        # Creating WebDriverWait object that sets poll freq of every 1sec with a 60sec wait until timeout
        return WebDriverWait(self.nadlan_driver, timeout=60, poll_frequency=1.0)

    # Create our Nadlan dictionary --> Set the key names of the dictionary
    def create_data_dict_keys(self) -> dict[str, list]:
        return {
            "Sale_Date": [],
            "City": [],
            "Neighborhood": [],
            "Street": [],
            "Building_Number": [],
            "Property_Type": [],
            "Rooms": [],
            "Floor": [],
            "Square_Meter": [],
            "Price": []
        }

    # Reset the data from our Nadlan dictionary
    def reset_dict_data(self) -> None:
        self.nadlan_dict = {key: [] for key in self.nadlan_dict.keys()}

    # This is where combine and perform our three main scraping operations:
    # 1. City Scraper --> To gain a scraping accesses to the neighborhoods in each city
    # 2. Neighborhood Scraper --> To gain a scraping accesses to the housing units in each Neighborhood
    # 3. Housing Units Scraper --> Where we collect the data!
    def main_scraper(self) -> None:
        # Iterate through each city
        for city_num in range(self.NUM_OF_CITIES):
            self.display_neighborhood_table()
             # Enter the current city page and get its name
            city_name = self.scrape_city(idx=city_num)
            # Iterate through each neighborhood in the city
            for neighborhood_num in range(self.get_number_of_neighborhoods()): # range(self.get_number_of_neighborhoods())
                # Enter the current neighborhood page
                neighborhood_name = self.scrape_neighborhood(idx=neighborhood_num)
                 # If there are no more neighborhood in the city, break out of the loop
                if neighborhood_name is None: break
                # Collect data for all the housing units in the current neighborhood
                self.scrape_all_housing_units(city_name, neighborhood_name)
                # Store the collected data to a CSV file
                self.store_the_dict_in_the_df()
                self.nadlan_df.to_csv("Test2.csv")
                self.reset_dict_data()
                # Go back to the current city's neighborhoods page
                self.exit_to_the_previous_page()
                self.display_neighborhood_table()
            # Go back to the cities page
            self.exit_to_the_previous_page()
        # Store any remaining data & Write the final data to a CSV file
        self.store_the_dict_in_the_df()
        self.nadlan_df.to_csv("Test.csv")
            
    # This method navigates to the specified city after clicking on the corresponding button.
    # After getting the button element for the city's neighborhoods page, it returns the city's name
    def scrape_city(self, idx: int) -> str:
        # Find all the city buttons presented in the current page
        # (we do it because everytime a new page is loaded, the previous elements become stale)
        try:
            time.sleep(5)
            # button.text -> means that we are searching for elements with a tag name of button who stands in the 'text' css class
            cities_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'button.text')))
        except:
            cities_buttons_list = [] # ignore
            print("Failure in 'scrape_city' method!")
            self.close_nadlan_driver()
        city_name = cities_buttons_list[idx].text[8::]
        self.enter_page(cities_buttons_list[idx])
        return city_name

    # This method navigates to the specified neighborhood after clicking on the corresponding button.
    # If the button is empty (indicating there are no more neighborhoods), it returns None.
    # Otherwise, it scrolls to the bottom of the page and returns a list of rows that contains the data
    # of the housing units on the neighborhood.
    def scrape_neighborhood(self, idx: int) -> None | str:
        try:
            time.sleep(5)
            # button.text -> means that we are searching for elements with a tag name of button who stands in the 'text' css class
            neighborhoods_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'button.text')))
        except:
            neighborhoods_buttons_list = [] # ignore
            print("Failure in 'scrape_neighborhood' method!")
            self.close_nadlan_driver()
        neighborhood_name = neighborhoods_buttons_list[idx].text
        if idx == 0:
            # This condition is necessary for extracting the first neighborhood name because of the way the website is programmed
            neighborhood_name = neighborhood_name[6::]
        # If there are no more neighborhoods, return None
        if self.is_button_empty(neighborhood_name):
            return None
        # Go to the neighborhood page and wait for it to reload
        self.enter_page(neighborhoods_buttons_list[idx])
        # Scroll to the bottom of the page so that all the data can get loaded onto the page
        self.scroll_to_the_bottom_of_the_page()
        # Return a list of rows that contains the data of the housing units on the street
        return neighborhood_name

    # This method iterate through each housing unit in the current neighborhood
    # and gain acessess to its data in-order to store it in our dictionary
    def scrape_all_housing_units(self, city_name: str, neighborhood_name: str) -> None:
        data_list = self.nadlan_driver.find_elements(By.CSS_SELECTOR, "div.tableCol")
        print("current amount of housing units (more or less) = ", len(data_list)//10)
        count_data_collected = 0
        for i in range(0, len(data_list), 10):
            # Collect the data from the current housing unit
            self.collect_data(data_list, i, city_name, neighborhood_name)
            print("collected data ", count_data_collected)
            count_data_collected += 1
    
    # This method scroll to the bottom of the
    # page that the web driver is set on in-order
    # to load all the page's content
    def scroll_to_the_bottom_of_the_page(self) -> None:
        # Get the initial height of the page, and make first scroll
        stuck_counter = 0
        previous_height = self.nadlan_driver.execute_script('return document.body.scrollHeight')
        self.nadlan_driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        time.sleep(2)
        new_height = self.nadlan_driver.execute_script('return document.body.scrollHeight')
        if previous_height == new_height: stuck_counter += 1
        # Keep scrolling until the page stops changing height
        # (meaning that we have reached the bottom of the page)
        while stuck_counter < 6:
            # Update the previous height for the next scroll
            previous_height = new_height
            self.nadlan_driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(2)
            new_height = self.nadlan_driver.execute_script('return document.body.scrollHeight')
            if previous_height == new_height: stuck_counter += 1

    # This is where we collect the data of the specified housing unit.
    # The complexity of the Nadlan web page and our  lack of knowledge of
    # the HTML language forced us to collect the data manually

    def collect_data(self, housing_unit_data: list[WebElement], idx: int, city_name: str, neighborhood_name: str) -> None:
        self.nadlan_dict["City"].append(city_name)
        self.nadlan_dict["Neighborhood"].append(neighborhood_name)
        self.nadlan_dict["Sale_Date"].append(housing_unit_data[idx].text)
        if len(housing_unit_data[idx+1].text.split()) > 0:
            self.nadlan_dict["Street"].append((housing_unit_data[idx+1].text.strip()).rsplit(' ', 1)[0])
            self.nadlan_dict['Building_Number'].append((housing_unit_data[idx+1].text.strip()).rsplit(' ', 1)[1])
        else:
            # If there is no address for the current apartment record
            # we will insert np.nan instead
            self.nadlan_dict['Street'].append(np.nan)
            self.nadlan_dict['Building_Number'].append(np.nan)
        self.nadlan_dict["Property_Type"].append(housing_unit_data[idx+3].text)
        self.nadlan_dict["Rooms"].append(housing_unit_data[idx+4].text)
        self.nadlan_dict["Floor"].append(housing_unit_data[idx+5].text)
        self.nadlan_dict["Square_Meter"].append(housing_unit_data[idx+6].text)
        self.nadlan_dict["Price"].append(housing_unit_data[idx+7].text)

    # For the page to contain table data of neighborhoods and not streets
    def display_neighborhood_table(self) -> None:
        try:
            time.sleep(5)
            neighborhoods_button = self.wait().until(EC.presence_of_all_elements_located((By.TAG_NAME,"button")))[10]
            neighborhoods_button.click()
        except:
            print("Failure in 'display_neighborhood_table' method!")


    def get_number_of_neighborhoods(self) -> int:
        try:
            time.sleep(5)
            neighborhoods_buttons_list = self.wait().until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"button.text")))
        except:
            print("Failure in 'get_number_of_neighborhoods' method!")
        finally:
            return len(neighborhoods_buttons_list)


    # Check if the text in a given button element is empty
    def is_button_empty(self, button_text: str) -> bool:
        # Return True if the first character of the button's text is a space
        return button_text[0] == " "

    # Click on a given button element and wait for it to reload
    def enter_page(self, button: WebElement) -> None:
        button.click()

    # Go back to the previous page and wait for it to reload
    def exit_to_the_previous_page(self) -> None:
        self.nadlan_driver.back()

    # Store the contents of the nadlan_dict dictionary in the nadlan_df dataframe
    def store_the_dict_in_the_df(self) -> None:
        self.nadlan_df = self.nadlan_df.append(pd.DataFrame.from_dict(self.nadlan_dict))

    # Where we close the web driver and end the crawling
    def close_nadlan_driver(self) -> None:
        self.nadlan_driver.close()
        print("Finished Crawling!")
        exit(1)