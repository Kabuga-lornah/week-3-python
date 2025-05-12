import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import csv
import numpy as np


source_currency = input("Enter source currency (e.g. USD): ").strip().upper()
if not source_currency:
    source_currency = "USD"

target_currency = input("Enter target currency (e.g. KES): ").strip().upper()
if not target_currency:
    print("Target currency cannot be empty.")
    exit()

api_key = input("Enter your ExchangeRate-API key: ").strip()
if not api_key:
    print("API key is required.")
    exit()


headers = {
    'User-Agent': 'Mozilla/5.0'
}

products = []
try:
    url = "https://www.jumia.co.ke/phones-tablets/smartphones/"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    items = soup.select("article.prd")

    for item in items:
        title_tag = item.select_one("h3.name")
        price_tag = item.select_one("div.prc")

        if title_tag and price_tag:
            title = title_tag.text.strip()
            price_text = price_tag.text.replace("KSh", "").replace(",", "").strip()

            try:
                price_kes = float(price_text)
                products.append({
                    'Product Name': title,
                    'Price (KES)': price_kes
                })
            except ValueError:
                continue

except requests.exceptions.RequestException as e:
    print(f"Connection error: {e}")
    exit()

if not products:
    print("No products found. Exiting.")
    exit()


csv_filename = "jumia_products_kes.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['Product Name', 'Price (KES)'])
    writer.writeheader()
    writer.writerows(products)

print(f"Scraped product data saved to '{csv_filename}'.")


df = pd.DataFrame(products)

try:
 
    conversion_url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{source_currency}/{target_currency}"
    response = requests.get(conversion_url)
    data = response.json()

    if data.get('result') != 'success':
        print(f"API Error: {data.get('error-type', 'Unknown error')}")
        exit()

    rate = data['conversion_rate']
    print(f"\nExchange Rate: 1 {source_currency} = {rate} {target_currency}")

except Exception as e:
    print(f"Conversion error: {e}")
    exit()

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df[f'Price ({source_currency})'] = (df['Price (KES)'] / rate).round(2)
df['Timestamp'] = timestamp

processed_csv_filename = 'jumia_product_prices.csv'
df.to_csv(processed_csv_filename, index=False)
print(f"Processed prices saved to '{processed_csv_filename}'.")


print(f"\n{'-'*40}\nJumia Product Prices (as of {timestamp}):\n{'-'*40}")
print(df[['Product Name', 'Price (KES)', f'Price ({source_currency})']].head(10).to_string(index=False))


plot_df = df.head(10)
titles = plot_df['Product Name']
titles_short = [title if len(title) < 20 else title[:17] + "..." for title in titles]

x = np.arange(len(titles_short))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 7))
rects1 = ax.bar(x - width/2, plot_df['Price (KES)'], width, label='KES', color='#4e79a7')
rects2 = ax.bar(x + width/2, plot_df[f'Price ({source_currency})'], width, label=source_currency, color='#f28e2b')

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:,.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

autolabel(rects1)
autolabel(rects2)

ax.set_ylabel('Price')
ax.set_title(f'Price Comparison: KES vs {source_currency}')
ax.set_xticks(x)
ax.set_xticklabels(titles_short, rotation=30, ha='right', fontsize=10)
ax.legend()
plt.tight_layout()
plt.savefig('jumia_price_comparison.png')
plt.show()
