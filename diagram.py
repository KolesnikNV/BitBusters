from diagrams import Cluster, Diagram
from diagrams.programming.language import Python

with Diagram("Async Parser Flow", show=False):
    with Cluster("Async Functions"):
        fetch = Python("fetch")
        parse_products = Python("parse_products")
        process_file_name = Python("process_file_name")
        fetch_product_data = Python("fetch_product_data")
        extract_spec_values = Python("extract_specification_values")
        extract_image_urls = Python("extract_image_urls")
        extract_video_url = Python("extract_video_url")
        extract_size_price = Python("extract_size_price")
        extract_product_attrs = Python("extract_product_attributes")
        fetch_urls = Python("fetch_urls")
        create_excel = Python("create_excel")
        process_data_async = Python("process_data_async")

    fetch >> parse_products >> fetch_urls >> fetch_product_data >> extract_product_attrs
    fetch_product_data >> extract_spec_values
    fetch_product_data >> extract_image_urls
    fetch_product_data >> extract_video_url
    fetch_product_data >> extract_size_price
    extract_product_attrs >> create_excel
    fetch_urls >> create_excel
    create_excel >> process_data_async

    with Cluster("Other Dependencies"):
        os_module = Python("os")
        openpyxl_module = Python("openpyxl")
        httpx_module = Python("httpx")
        halo_module = Python("halo")
        tqdm_module = Python("tqdm")

    os_module >> fetch_product_data
    openpyxl_module >> create_excel
    httpx_module >> fetch
    halo_module >> process_data_async
    tqdm_module >> process_data_async
