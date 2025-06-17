import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Extract numeric price from text
def extract_price(text):
    if text:
        match = re.search(r'[\d,.]+', text.replace(',', ''))
        if match:
            return float(match.group().replace(',', ''))
    return None

# Extract numeric rating from text
def extract_rating(text):
    if text:
        match = re.search(r'\d+(\.\d+)?', text)
        if match:
            return float(match.group())
    return None


def scrape_ecommerce(url):
    print(f"\nScraping: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    titles, prices, ratings = [], [], []

    # Try to extract all product cards
    product_tags = soup.find_all(['div', 'article'], class_=lambda c: c and ('product' in c.lower() or 'card' in c.lower() or 'item' in c.lower()))

    if not product_tags:
        print("No product cards found, trying fallback search.")
        product_tags = soup.find_all('div')

    for tag in product_tags:
        text = tag.get_text(separator=' ', strip=True)

        title = tag.find(['h2', 'h3', 'span', 'a'])
        price = re.search(r'[$₹€£]\s?\d{1,3}(?:[,\d{3}]*)(?:\.\d{1,2})?', text)
        rating = re.search(r'\d\.\d|out of \d', text)

        titles.append(title.get_text(strip=True) if title else None)
        prices.append(extract_price(price.group()) if price else None)
        ratings.append(extract_rating(rating.group()) if rating else None)

    df = pd.DataFrame({'Title': titles, 'Price': prices, 'Rating': ratings})
    return df


def analyze_data(df):
    print("\nSummary Statistics:")
    print(df.describe(include='all'))

    df_clean = df.dropna(subset=['Title', 'Price'])

    if df_clean.empty:
        print("No usable product data found.")
        return


    df_clean.to_csv("ecommerce_cleaned_data.csv", index=False)
    print("\nSaved cleaned data to ecommerce_cleaned_data.csv")


    plt.figure(figsize=(8, 4))
    sns.histplot(df_clean['Price'], kde=True)
    plt.title("Price Distribution")
    plt.xlabel("Price")
    plt.tight_layout()
    plt.grid()
    plt.show()

    if 'Rating' in df_clean.columns and df_clean['Rating'].notna().sum() > 0:
        plt.figure(figsize=(6, 4))
        sns.scatterplot(x='Rating', y='Price', data=df_clean)
        plt.title("Price vs Rating")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


def main():
    url = input("Enter e-commerce URL: ").strip()
    df = scrape_ecommerce(url)

    print("\nRaw Data Preview:")
    print(df.head())

    analyze_data(df)

if __name__ == "__main__":
    main()
