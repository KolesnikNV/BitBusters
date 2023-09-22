import os
import asyncio

import pandas as pd
import aiohttp
import ssl

sslcontext = ssl.create_default_context()
sslcontext.check_hostname = False
sslcontext.verify_mode = ssl.CERT_NONE
BASE_URL = "https://jewelers.services/productcore/api/"
BASE_MEDIA_URL = "https://images.jewelers.services"

CATEGORIES = ("Jewelry-Rings-2·Stone-Rings", "Jewelry-Rings-Adjustable")
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
}


async def get_urls(session, url, headers, category):
    """
    Возвращает список эндпоинтов каждого товара на странице.
    """
    body = {
        "filters": [{"key": "ItemsPerPage", "value": "36"}],
        "page": 1,
        "sortCode": 28420,
        "path": f"{category}",
    }
    async with session.post(url, headers=headers, json=body) as response:
        src = await response.json()

    return [
        f"{BASE_URL}pd/{item.get('URLDescription')}/{item.get('Style')}"
        for item in src["IndexedProducts"]["Results"]
    ]


async def get_data(session, url, headers):
    """Получает и возвращает данные по указанному URL-адресу в формате JSON"""
    try:
        async with session.get(url, headers=headers, ssl=False, timeout=30) as response:
            response.raise_for_status()
            return await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"Не удалось получить данные по адресу {url}: {str(e)}")
        return None


async def get_specification(session, url, headers, category):
    """
    Получает необходимые данные для каждого товара по его URL, компонует все
    данные в список
    """
    products_data = []
    urls = await get_urls(session, url, headers, category)
    for item_url in urls:
        print(f"Получение данных по адресу: {item_url}")
        data = await get_data(session, item_url, headers)
        if data:
            description = {}
            product = data.get("Product")
            if product:
                description["Product"] = product["Style"]
                description["CountryOfOrigin"] = product["CountryOfOrigin"]
                description["Product availability"] = (
                    "In Stock" if product["InStock"] > 0 else "Out of Stock"
                )
            specifications = data.get("Specifications")
            if specifications:
                description.update(
                    {
                        spec_item["Specification"]: spec_item["Value"]
                        for spec_item in specifications
                    }
                )
            sizes = data.get("Sizes")
            if sizes:
                description["Price_on_size"] = [
                    {"size": size["Size"], "MSRP": size["MSRP"]} for size in sizes
                ]
            images = data.get("Images")
            if images:
                description["Images"] = {
                    f"{BASE_MEDIA_URL}/qgrepo/{img.get('FileName')}" for img in images
                }
            video = data.get("Video")
            if video:
                description["Video"] = f"{BASE_MEDIA_URL}/0/Videos/{video['FileName']}"
            products_data.append(description)
    return products_data


async def save_in_excel(data, category):
    """Создание файла .xlsx и заполнение его данными"""
    df = pd.DataFrame(data)
    directory = "./output"
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"{category}.xlsx")
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, df.to_excel, file_path)
    except Exception as e:
        print(f"Не удалось сохранить данные в файл {file_path}: {str(e)}")


async def parse_category(session, url, category):
    """
    Выполняет парсинг товаров из указанной категории.

    """
    data = await get_specification(session, url, HEADERS, category)
    if data:
        await save_in_excel(data, category)


async def main():
    """
    Главная функция, запускает парсинг двух категорий параллельно.
    """
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=sslcontext)
    ) as session:
        tasks = []
        for category in CATEGORIES:
            url = BASE_URL + f"pl/{category}"
            task = asyncio.create_task(parse_category(session, url, category))
            tasks.append(task)

        await asyncio.gather(*tasks)


async def cyclic_parse():
    """Выполнение парсинга с заданной в минутах периодичностью"""
    interval = int(input("Введите периодичность парсинга в минутах: "))
    while True:
        print("Начало парсинга")
        await main()
        print("Данные сохранены. Ожидание следующего цикла")
        await asyncio.sleep(interval * 60)


if __name__ == "__main__":
    try:
        asyncio.run(cyclic_parse())
    except KeyboardInterrupt:
        pass
