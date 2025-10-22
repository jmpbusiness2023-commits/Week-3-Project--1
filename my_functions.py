# my_functions.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Function to scrape The Numbers and return a DataFrame
def scrape_the_number(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    rcs = requests.get(url, headers=headers)
    soup = BeautifulSoup(rcs.text, "html.parser")
    rows = soup.select("table tr")
    data = []

    for row in rows:
        cells = row.find_all("td")
        if cells:
            data.append([cell.text.strip() for cell in cells])

    df = pd.DataFrame(
        data,
        columns=[
            "Index",
            "Release Date",
            "Title",
            "Production Budget",
            "Domestic Gross",
            "Worldwide Gross",
        ],
    )
    return df


# 2. Function to get movie info from OMDB API
key = "2f9babf3"

def get_movie_info(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={key}"
    res = requests.get(url).json()
    time.sleep(0.2)
    return res

def clean_movie_data(movie_df):
    # Standardize column names
    movie_df.columns = movie_df.columns.str.lower().str.replace(' ', '_')

    # Handle missing values
    movie_df.fillna({'release_date': 'Unknown', 'overview': 'No overview available'}, inplace=True)

    # Remove duplicates but we need to fix the issue with dropping almost 800 rows
    # movie_df.drop_duplicates(subset='title', keep='first', inplace=True)

    # Convert data types if needed
    # For example, convert release_date to datetime
    movie_df['release_date'] = pd.to_datetime(movie_df['release_date'], errors='coerce')

    return movie_df


def visualize_movies(df):
    
    # --- 📊 Simple Visualization ---
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        data=df,
        x="production_budget",
        y="worldwide_gross",
        hue="title",
        size="worldwide_gross",
        legend=False,
        alpha=0.6
    )
    plt.title("Budget de production vs Revenu mondial", fontsize=14, weight='bold')
    plt.xlabel("Production Budget ($)")
    plt.ylabel("Worldwide Gross ($)")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # --- 📈 Top 10 most profitable movies ---
    df_cleaned["profit"] = df_cleaned["worldwide_gross"] - df_cleaned["production_budget"]
    top10 = df_cleaned.sort_values(by="profit", ascending=False).head(10)

    plt.figure(figsize=(10, 5))
    sns.barplot(
        data=top10,
        x="profit",
        y="title",
        orient="h"
    )
    plt.title("Top 10 des films les plus rentables 💰", fontsize=14, weight='bold')
    plt.xlabel("Profit ($)")
    plt.ylabel("Titre du film")
    plt.tight_layout()
    plt.show()