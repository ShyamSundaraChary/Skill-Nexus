import requests
from bs4 import BeautifulSoup

# Load proxies
with open("working_proxies.txt", "r") as f:
    proxies = f.read().splitlines()

# Websites to scrape
sites_to_check = [
    "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html",
    "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html"
]

cnt = 0  # Counter for proxies

for site in sites_to_check:
    try:
        print(f"Using proxy: {proxies[cnt]}")
        
        res = requests.get(site, proxies={"http": proxies[cnt], "https": proxies[cnt]})
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")

            # Extract title
            title = soup.find("h1").text.strip()

            # Extract price (if available)
            price_tag = soup.find(class_="price_color")
            price = price_tag.text.strip() if price_tag else "No price found"

            # Extract availability
            stock_tag = soup.find(class_="instock availability")
            stock = stock_tag.text.strip() if stock_tag else "Stock info not found"

            print(f"Title: {title}")
            print(f"Price: {price}")
            print(f"Availability: {stock}")
            print("-" * 40)
        else:
            print(f"Failed to fetch {site} | Status Code: {res.status_code}")

    except Exception as e:
        print(f"Proxy {proxies[cnt]} failed | Error: {e}")

    finally:
        cnt += 1
