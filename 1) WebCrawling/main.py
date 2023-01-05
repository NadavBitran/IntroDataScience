from NadlanScraper import NadlanScraper

def main():
    scraper = NadlanScraper()
    scraper.main_scraper()
    scraper.close_nadlan_driver()


if __name__ == '__main__':
    main()

