import csv
import json
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import ssl

sslcontext = ssl.create_default_context()
sslcontext.check_hostname = False
sslcontext.verify_mode = ssl.CERT_NONE


async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()


class SeleniumScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(
            options=chrome_options,
        )

    def scrape_product(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "heading"))
            )
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            product_name = soup.find("h3", class_="heading").text.strip()
            sizes = []
            prices = []

            size_price_container = soup.find("ul", class_="sizes-list")
            for button in size_price_container.find_all("button", class_="size-item"):
                size = button.find("span", class_="size-number").text.strip()
                price_span = button.find("p", class_="price-tooltip").find_all("span")[
                    1
                ]
                price = price_span.text.strip()
                sizes.append(size)
                prices.append(price)

            msrp = (
                soup.find("div", class_="price-tag msrp")
                .find("p", class_="value")
                .text.strip()
            )
            availability = soup.find("p", class_="price-tag available-msg").text.strip()

            specs = {}
            for spec_row in soup.select(".specs-table-wrapper ul.table li.trow"):
                label = spec_row.find("p", class_="label").text.strip()
                value = spec_row.find("p", class_="value").text.strip()
                specs[label] = value

            product_data = {
                "Product Name": product_name,
                "Sizes": ", ".join(sizes),
                "Prices": ", ".join(prices),
                "MSRP": msrp,
                "Availability": availability,
                "Specifications": json.dumps(specs),
            }

            return product_data

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")

    def close(self):
        self.driver.quit()


async def scrape_product_data(url, csv_writer, session, scraper):
    try:
        # Используйте ваш экземпляр класса SeleniumScraper для извлечения данных
        product_data = scraper.scrape_product(url)
        if product_data:
            csv_writer.writerow(product_data)
            print(f"Result for URL {url}:\n{product_data}\n\n")

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")


async def main():
    urls = [
        "https://qgold.com/pd/Sterling-Silver-Antiqued-Polished-Textured-Full-Finger-Adjustable-Ring/QR6116",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Adjustable-Ring/QR6718-6",
        "https://qgold.com/pd/Sterling-Silver-Antiqued-Adjustable-Toe-Ring/QR852",
        "https://qgold.com/pd/Sterling-Silver-Polished-Half-Moon-and-Star-Adjustable-Ring/QR6191",
        "https://qgold.com/pd/Sterling-Silver-Polished-Twisted-Bar-Center-Adjustable-Cuff-Ring/QR6588-6",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Square-and-Circle-Adjustable-Ring/QR6682",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-Polished-CZ-Arrow-Ring/QR6205",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-CZ-Stars-Bypass-Adjustable-Ring/QR7181",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-Bar-and-Chain-Link-Adjustable-Ring/QR7516-6",
        "https://qgold.com/pd/14K-Two-tone-Gold-Woven-Mesh-Stretch-Ring/SF2822",
        "https://qgold.com/pd/Sterling-Silver-Polished-CZ-Butterfly-Double-Finger-Ring/QR6660-6",
        "https://qgold.com/pd/Lacquer-Dipped-Red-Real-Rose-Adjustable-Silver-tone-Ring/BF1327",
        "https://qgold.com/pd/10k-Gold-Polished-Cat-Adjustable-Cuff-Ring/10R639",
        "https://qgold.com/pd/Sterling-Silver-Adjustable-Polished-Ring/QR793",
        "https://qgold.com/pd/Sterling-Silver-Green-Glass-Bead-4-Leaf-Clover-Adjustable-Ring/QR6330",
        "https://qgold.com/pd/Sterling-Silver-Polished-Half-Moon-and-Sun-Orange-CZ-Adjustable-Ring/QR6321",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Key-Adjustable-Ring/QR6747",
        "https://qgold.com/pd/Sterling-Silver-Flash-Gold-plated-Textured-Twist-Adjustable-Ring/QR7514GP",
        "https://qgold.com/pd/14K-Gold-Twisted-Woven-Mesh-Stretch-Ring/SF2821",
        "https://qgold.com/pd/1928-Silver-tone-Black-Enamel-and-Black-Crystal-Vintage-Vine-Pattern-Stretch-Ring/BF1105",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Adjustable-Ring/QR6522",
        "https://qgold.com/pd/Sterling-Silver-Polished-Love-Adjustable-Ring/QR6068",
        "https://qgold.com/pd/Leslies-Sterling-Silver-Rhodium-Plated-Adjustable-Ring/QLR112",
        "https://qgold.com/pd/Swarovski-Crystal-Macrame-Ring/SR0651-34",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-Stars-Adjustable-Ring/QR7182",
        "https://qgold.com/pd/Sterling-Silver-Polished-and-Antiqued-Adjustable-Ring/QR6111",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-August-Light-Green-Triple-CZ-Adjustable-Ring/QR7186AUG",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-and-Textured-Adjustable-Ring/QR7524",
        "https://qgold.com/pd/Sterling-Silver-Polished-Synthetic-Pearl-Ring/QR7606-8",
        "https://qgold.com/pd/Leslies-Sterling-Silver-Rhodium-plated-Adjustable-Ring/QLR115",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-Adjustable-Polished-CZ-Arrow-Ring/QR6207",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Adjustable-Fingernail-Ring/QR6687",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-November-Yellow-Triple-CZ-Adjustable-Ring/QR7186NOV",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-plated-CZ-Adjustable-Fingernail-Ring/QR6688",
        "https://qgold.com/pd/Sterling-Silver-Rhodium-Plated-November-Yellow-CZ-Adjustable-Ring/QR7185NOV",
    ]

    fieldnames = [
        "Product Name",
        "Sizes",
        "Prices",
        "MSRP",
        "Availability",
        "Specifications",
    ]

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=sslcontext)
    ) as session:
        async with aiofiles.open(
            "product_data.csv", mode="w", newline="", encoding="utf-8"
        ) as csvfile:
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csv_writer.writeheader()
            scraper = SeleniumScraper()

            tasks = []
            for url in urls:
                task = scrape_product_data(url, csv_writer, session, scraper)
                tasks.append(task)

            await asyncio.gather(*tasks)
            scraper.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
