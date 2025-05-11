import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import csv
import numpy as np


source_currency = input("Enter source currency (e.g. GBP): ").strip().upper()
if not source_currency:
    source_currency = "GBP"

target_currency = input("Enter target currency (e.g. KES): ").strip().upper()
if not target_currency:
    print("Target currency cannot be empty.")
    exit()

api_key = input("Enter your ExchangeRate-API key: ").strip()
if not api_key:
    print("API key is required.")
    exit()

headers = {'User-Agent': 'Mozilla/5.0'}


books = []
try:
    url = "https://books.toscrape.com/catalogue/page-1.html"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find_all('article', class_='product_pod')

    for book in articles:
        title = book.h3.a['title']
        price_text = book.find('p', class_='price_color').text
        
        price_text = price_text.replace('£', '').replace('\xa0', '').strip()
        try:
            price = float(price_text)
            books.append({
                'Title': title,
                f'Price ({source_currency})': price
            })
        except ValueError:
            continue

except requests.exceptions.RequestException as e:
    print(f"Connection error: {e}")
    exit()

if not books:
    print("No books found. Exiting.")
    exit()


csv_filename = "bookslibrary.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['Title', f'Price ({source_currency})'])
    writer.writeheader()
    writer.writerows(books)

print(f"Scraped book data saved to '{csv_filename}'.")

df = pd.DataFrame(books)

print("DataFrame columns:", df.columns.tolist())

price_col = f'Price ({source_currency})'
if price_col not in df.columns:
    print(f"Error: Expected column '{price_col}' not found in data.")
    exit()


try:
    conversion_url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{source_currency}/{target_currency}"
    response = requests.get(conversion_url)
    data = response.json()
    
    if data.get('result') != 'success':
        print(f"API Error: {data.get('error-type', 'Unknown error')}")
        exit()
    
    rate = data['conversion_rate']
except Exception as e:
    print(f"Conversion error: {e}")
    exit()

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df[f'Price ({target_currency})'] = (df[price_col] * rate).round(2)
df['Timestamp'] = timestamp


processed_csv_filename = 'book_prices.csv'
df.to_csv(processed_csv_filename, index=False)
print(f"Processed book prices saved to '{processed_csv_filename}'.")


print(f"\n{'-'*40}\nLatest Book Prices (as of {timestamp}):\n{'-'*40}")
print(df[['Title', price_col, f'Price ({target_currency})']].head(10).to_string(index=False))


plot_df = df.head(10)
titles = plot_df['Title']


titles_short = [title if len(title) < 20 else title[:17] + "..." for title in titles]

x = np.arange(len(titles_short))  
width = 0.35 

fig, ax = plt.subplots(figsize=(14, 7))

rects1 = ax.bar(x - width/2, plot_df[price_col], width, label=source_currency, color='#4e79a7')
rects2 = ax.bar(x + width/2, plot_df[f'Price ({target_currency})'], width, label=target_currency, color='#f28e2b')


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
ax.set_title(f'Price Comparison: {source_currency} vs {target_currency}')
ax.set_xticks(x)
ax.set_xticklabels(titles_short, rotation=30, ha='right', fontsize=10)
ax.legend()
plt.tight_layout()
plt.savefig('price_comparison.png')
plt.show()
