import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import multiprocessing


class MainPageScraper:
    def __init__(self, url):
        self.url = url
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def scrape(self):
        self.driver.get(self.url)
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div > p.description > span")
            )
        )

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.find_all(
            "div",
            class_="col-lg-3 col-md-4 col-sm-4 product-item ng-star-inserted",
        )

        results = []
        for element in elements:
            product_link = (
                product_link_element["href"]
                if (product_link_element := element.find("a", class_="image-thumbnail"))
                else "N/A"
            )
            if product_link.startswith("/pd/"):
                results.append(product_link)

        return results

    def close(self):
        self.driver.quit()


def scrape_and_write(url):
    scraper = MainPageScraper(url)
    data = scraper.scrape()
    scraper.close()
    return data


if __name__ == "__main__":
    base_url = "https://qgold.com/pl/Jewelry-Rings-Adjustable"

    pool = multiprocessing.Pool(processes=8)
    a = scrape_and_write(base_url)
    print(a)
    pool.close()
    pool.join()
