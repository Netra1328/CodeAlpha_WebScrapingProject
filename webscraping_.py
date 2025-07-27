# 📦 Install required packages
!pip install -q requests gspread gspread_dataframe oauth2client pdfkit
!apt-get install -y wkhtmltopdf > /dev/null

import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from IPython.display import display, FileLink
import os

# -------------------- SCRAPING FUNCTIONS --------------------

def scrape_quotes_fast(base_url, max_pages=3):
    all_quotes = []
    page = 1
    while page <= max_pages:
        url = f"{base_url}/page/{page}/"
        print(f"📄 Scraping page {page}...")
        response = requests.get(url)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        quotes = soup.find_all("div", class_="quote")
        if not quotes:
            break
        for quote in quotes:
            text = quote.find("span", class_="text").text.strip()
            author = quote.find("small", class_="author").text.strip()
            tags = [tag.text for tag in quote.find_all("a", class_="tag")]
            all_quotes.append({
                "Quote": text,
                "Author": author,
                "Tags": ", ".join(tags)
            })
        page += 1
    return pd.DataFrame(all_quotes)

def scrape_books_fast(base_url, max_pages=3):
    all_books = []
    page = 1
    while page <= max_pages:
        url = f"{base_url}/catalogue/page-{page}.html"
        print(f"📄 Scraping page {page}...")
        response = requests.get(url)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        books = soup.find_all("article", class_="product_pod")
        if not books:
            break
        for book in books:
            title = book.h3.a["title"]
            price = book.find("p", class_="price_color").text.strip()
            rating = book.p["class"][1] if len(book.p["class"]) > 1 else "Unknown"
            all_books.append({
                "Title": title,
                "Price": price,
                "Rating": rating
            })
        page += 1
    return pd.DataFrame(all_books)

# -------------------- MAIN EXECUTION --------------------

print("\n🌐 Choose website to scrape:")
print("1) Quotes")
print("2) Books")
site_choice = input("👉 Enter 1 or 2: ").strip()

if site_choice == '1':
    print("\n🔄 Scraping Quotes...")
    df = scrape_quotes_fast("http://quotes.toscrape.com", max_pages=3)
    print("\n📋 Dataset After Scraping (Quotes):")
    display(df.head(10))

    # 🔍 Filter by Author
    author_input = input("\n✍️ Enter author name to filter (or press Enter to skip): ").strip()
    if author_input:
        df = df[df["Author"].str.lower() == author_input.lower()]

    # 🔖 Filter by Tag
    tag_input = input("🔖 Enter tag to filter (or press Enter to skip): ").strip()
    if tag_input:
        df = df[df["Tags"].str.contains(tag_input, case=False)]

    # 📊 Show bar chart of top authors
    if not df.empty:
        print("\n📊 Top Authors:")
        top_authors = df["Author"].value_counts().head(5)
        top_authors.plot(kind='bar', color='skyblue')
        plt.title("Top 5 Authors")
        plt.xlabel("Author")
        plt.ylabel("Quotes")
        plt.grid(True)
        plt.show()

elif site_choice == '2':
    print("\n🔄 Scraping Books...")
    df = scrape_books_fast("http://books.toscrape.com", max_pages=3)
    print("\n📋 Dataset After Scraping (Books):")
    display(df.head(10))
else:
    print("⚠️ Invalid choice. Exiting...")
    exit()

# -------------------- SAVE OPTIONS --------------------

if not df.empty:
    print("\n💾 How do you want to save the data?")
    print("1) CSV")
    print("2) PDF")
    print("3) Google Sheets")
    choice = input("👉 Enter 1, 2 or 3: ").strip()

    file_base = "scraped_data"

    if choice == '1':
        file_name = f"{file_base}.csv"
        df.to_csv(file_name, index=False, encoding='utf-8')
        print(f"\n✅ CSV saved as '{file_name}'")
        from google.colab import files
        files.download(file_name)

    elif choice == '2':
        file_html = f"{file_base}.html"
        file_pdf = f"{file_base}.pdf"
        df.to_html(file_html, index=False)
        import pdfkit
        config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
        pdfkit.from_file(file_html, file_pdf, configuration=config)
        print(f"\n✅ PDF saved as '{file_pdf}'")
        from google.colab import files
        files.download(file_pdf)

    elif choice == '3':
        print("🔗 Uploading to Google Sheets...")
        import gspread
        from google.colab import auth
        from oauth2client.client import GoogleCredentials
        from gspread_dataframe import set_with_dataframe

        auth.authenticate_user()
        gc = gspread.authorize(GoogleCredentials.get_application_default())

        sheet_name = input("📄 Enter Google Sheet name: ").strip() or "Scraped Data"
        sh = gc.create(sheet_name)
        worksheet = sh.get_worksheet(0)
        set_with_dataframe(worksheet, df)

        print(f"✅ Uploaded to Google Sheet: {sheet_name}")
        print("🔗 Open Sheets: https://sheets.google.com")
    else:
        print("⚠️ Invalid option selected.")
else:
    print("⚠️ No data to save.")
