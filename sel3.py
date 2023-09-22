import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

url = "https://qgold.com/pd/sterling-silver-rhodium-plated-cz-two-stone-polished-ring/qr6708-6"

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 2)

driver.get(url)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "row")))
images = driver.find_element(By.CLASS_NAME, "pd-img-container")
s = images.get_attribute("outerHTML")

soup = BeautifulSoup(s, "html.parser")
thumbnail_container = soup.find("div", class_="ngx-gallery-thumbnails")

# Ищем все ссылки на фотографии внутри контейнера
image_links = thumbnail_container.find_all("a", class_="ngx-gallery-thumbnail")

# Список для хранения ссылок на фотографии
image_urls = []

# Список для хранения ссылок на видео
video_urls = []

# Извлекаем ссылки на фотографии
for image_link in image_links:
    style_attribute = image_link["style"]
    image_url = style_attribute.split('url("')[1].split('")')[0]
    image_urls.append(image_url)

# Ищем и нажимаем на кнопки воспроизведения видео
video_link_containers = soup.find_all(
    "div", class_="col-3 col-sm-2 col-md-2 video_link_container"
)

for container in video_link_containers:
    if video_button := container.find("i", class_="fa fa-play-circle"):
        video_button.click()
        time.sleep(2)  # Подождем немного, чтобы видео успело загрузиться
        video_element = driver.find_element(By.TAG_NAME, "video")
        video_url = video_element.get_attribute("src")
        video_urls.append(video_url)

# Выводим найденные ссылки
print("Ссылки на фотографии:")
for i, image_url in enumerate(image_urls, 1):
    print(f"Фотография {i}: {image_url}")
print("Ссылки на видео:")
for i, video_url in enumerate(video_urls, 1):
    print(f"Видео {i}: {video_url}")

with open("43.html", "w") as file:
    file.write(s)
driver.quit()
