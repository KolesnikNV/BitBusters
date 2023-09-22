import asyncio
import os

import httpx
import openpyxl
from halo import Halo
from tqdm import tqdm

from core.settings import (
    Jewelry_Rings_Adjustable_fetch_params,
    Jewelry_Rings_Adjustable_fetch_url,
    Jewelry_Rings_Two_Stone_Rings_fetch_params,
    Jewelry_Rings_Two_Stone_Rings_fetch_url,
    params_request,
)


async def fetch(url: str, params: dict[str, any]) -> httpx.Response:
    """
    Выполняет асинхронный HTTP-запрос на указанный URL с заданными параметрами.
    """
    headers = params["headers"]
    body = params["body"]
    async with httpx.AsyncClient() as client:
        if params["method"] != "POST":
            return await client.get(url, headers=headers)
        return await client.post(url, headers=headers, data=body)


def parse_products(data: list[dict[str, any]]) -> list[str]:
    """
    Извлекает URL-адреса продуктов со страницы с товарами.
    """
    urls = []
    for product in data:
        url_description = product["URLDescription"]
        style = product["Style"]
        url = f"https://jewelers.services/productcore/api/pd/{url_description}/{style}"
        urls.append(url)
    return urls


def process_file_name(url: str) -> str:
    """
    Генерирует имя файла на основе URL-адреса.
    """
    file_name = os.path.basename(url)
    file_name = file_name.replace("?", "").replace("/", "_")
    file_name = file_name.split("=")[0] + ".xlsx"
    return file_name


async def fetch_product_data(url: str) -> dict:
    """
    Получает данные о продукте по URL.
    """
    response = await fetch(url, params_request)
    return {} if response.status_code != 200 else response.json()


def extract_specification_values(specifications: list[dict]) -> str:
    """
    Извлекает строку со спецификациями продукта из данных о продукте.
    """
    specification_values = []
    for spec in specifications:
        spec_name = spec.get("Specification")
        spec_value = spec.get("Value")
        specification_values.append(f"{spec_name}: {spec_value}")
    return "; ".join(specification_values)


def extract_image_urls(images: list[dict]) -> str:
    """
    Извлекает строку с URL-адресами изображений из данных о продукте.
    """
    image_names = [image.get("FileName") for image in images]
    image_urls = [
        f"https://images.jewelers.services/qgrepo/{image_name}"
        for image_name in image_names
    ]
    return "; ".join(image_urls)


def extract_video_url(video: dict) -> str:
    """
    Извлекает URL-адрес видео из данных о продукте.
    """
    video_filename = video.get("FileName") if video else "None"
    return (
        f"https://images.jewelers.services/0/Videos/{video_filename}"
        if video
        else "None"
    )


def extract_size_price(sizes: list[dict], product_data: dict) -> str:
    """
    Извлекает строку с размерами и ценами из данных о продукте.
    """
    if not sizes:
        return product_data.get("Product", {}).get("MSRP")
    size_price_list = [
        f"{size_data.get('Size')} - {size_data.get('MSRP')}" for size_data in sizes
    ]
    return "; ".join(size_price_list)


def extract_product_attributes(product_data: dict) -> list:
    """
    Извлекает атрибуты продукта из данных о продукте.
    """
    description = product_data.get("Product", {}).get("Description")
    sizes = product_data.get("Sizes")
    specifications = product_data.get("Specifications")
    images = product_data.get("Images")
    video = product_data.get("Video")
    availability = product_data.get("Product", {}).get("AvailabilityText")

    spec_string = extract_specification_values(specifications)
    image_string = extract_image_urls(images)
    video_url = extract_video_url(video)
    size_price_string = extract_size_price(sizes, product_data)

    return [
        description,
        size_price_string,
        spec_string,
        image_string,
        video_url,
        availability,
    ]


async def fetch_urls(urls: list[str]) -> list[list[str]]:
    """
    Получает данные для каждого URL-адреса продукта асинхронно.
    """
    data_list = []
    for url in urls:
        product_data = await fetch_product_data(url)
        if product_data:
            attributes = extract_product_attributes(product_data)
            data_list.append(attributes)
    return data_list


async def create_excel(file_name: str, data: list[list[str]]) -> None:
    """
    Создает новый файл Excel и сохраняет данные в него.
    """
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(
        ["Name", "Size - Price", "Specifications", "Images", "Video", "Availability"]
    )
    for row in data:
        worksheet.append(row)
    workbook.save(file_name)


jewelry_rings_adjustable_fetch = fetch(
    Jewelry_Rings_Adjustable_fetch_url, Jewelry_Rings_Adjustable_fetch_params
)

jewelry_rings_two_stone_rings_fetch = fetch(
    str(Jewelry_Rings_Two_Stone_Rings_fetch_url),
    Jewelry_Rings_Two_Stone_Rings_fetch_params,
)


async def process_data_async(fetch: httpx.Response) -> list[str]:
    """
    Обрабатывает данные о продуктах и сохраняет их в файл Excel.
    """
    response = await fetch
    result = response.json()
    if indexed_products := result.get("IndexedProducts"):
        if results := indexed_products.get("Results"):
            urls = parse_products(results)
            file_name = process_file_name(str(response.url))
            await create_excel(file_name, await fetch_urls(urls))
            return urls
        else:
            print("Нет данных о продуктах")
    else:
        print("Нет данных в IndexedProducts")


async def main():
    while True:
        times = int(
            input(
                "\nРаз в какое время вы хотите парсить данные? Введите время в минутах: "
            )
        )
        futures = []
        futures.append(process_data_async(jewelry_rings_adjustable_fetch))
        futures.append(process_data_async(jewelry_rings_two_stone_rings_fetch))

        with tqdm(total=len(futures), desc="\nПарсинг") as pbar:
            for completed_future in asyncio.as_completed(futures):
                await completed_future
                pbar.update(1)
        spinner = Halo(text="Ожидание следующего цикла...", spinner="dots")
        spinner.start()
        await asyncio.sleep(times * 60)
        spinner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nВы решили не дожидаться следующего цикла парсинга, печально :(")
