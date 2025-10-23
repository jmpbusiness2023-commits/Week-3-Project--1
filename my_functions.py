# Library imports
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt
import seaborn as sns
from textwrap import shorten

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

# 3. Function to clean the movie DataFrame
def clean_movie_data(movie_df):
    # Step 1: Drop unnecessary columns
    cols_to_drop = ['index', 'Index', 'Unnamed: 0', 'Unnamed: 0.1', 'Poster', 'Ratings', 'Released', 'Title_y', 'Type', 'Year']
    movie_df_cleaned = movie_df.drop(columns=cols_to_drop, errors='ignore').copy()

    # Step 2: Clean monetary columns
    money_cols = ["Domestic Gross", "Production Budget", "BoxOffice", "Worldwide Gross"]
    for c in money_cols:
        if c in movie_df_cleaned.columns:
            movie_df_cleaned[c] = (
                movie_df_cleaned[c]
                .astype(str)
                .str.replace(r"[\$,]", "", regex=True)
                .str.strip()
            )
            movie_df_cleaned[c] = pd.to_numeric(movie_df_cleaned[c], errors="coerce")

    # Step 3: Clean IMDb votes
    if "imdbVotes" in movie_df_cleaned.columns:
        movie_df_cleaned["imdbVotes"] = (
            movie_df_cleaned["imdbVotes"]
            .astype(str)
            .str.replace(",", "", regex=False)
        )
        movie_df_cleaned["imdbVotes"] = pd.to_numeric(movie_df_cleaned["imdbVotes"], errors="coerce")

    # Step 4: Clean numeric columns
    numeric_cols = ["Metascore", "imdbRating"]
    for c in numeric_cols:
        if c in movie_df_cleaned.columns:
            movie_df_cleaned[c] = pd.to_numeric(movie_df_cleaned[c], errors="coerce")

    # Step 5: Clean runtime
    if "Runtime" in movie_df_cleaned.columns:
        movie_df_cleaned["Runtime"] = (
            movie_df_cleaned["Runtime"]
            .astype(str)
            .str.extract(r"(\d+)", expand=False)
        )
        movie_df_cleaned["Runtime"] = pd.to_numeric(movie_df_cleaned["Runtime"], errors="coerce")

    # Step 6: Convert Release date to datetime format dd-mm-yyyy
    if "Release Date" in movie_df_cleaned.columns:
        movie_df_cleaned["Release Date"] = pd.to_datetime(
            movie_df_cleaned["Release Date"], errors="coerce", dayfirst=True
        ).dt.strftime("%d-%m-%Y")

    # Step 7: Rename columns for consistency
    rename_map = {
        'BoxOffice': 'Box_Office',
        'imdbID': 'imdb_ID',
        'Metascore': 'Meta_score',
        'imdbRating': 'imdb_Rating',
        'imdbVotes': 'imdb_Votes'
    }
    movie_df_cleaned = movie_df_cleaned.rename(columns=rename_map)

    # Step 8: Standardize column names
    movie_df_cleaned.columns = movie_df_cleaned.columns.str.lower().str.replace(' ', '_')

    # Step 9: Clean the Title column
    movie_df_cleaned['title'] = movie_df_cleaned['title'].astype(str).str.strip()  # remove leading/trailing spaces
    movie_df_cleaned['title'] = movie_df_cleaned['title'].str.replace(r'\s+', ' ', regex=True)  # remove multiple spaces
    movie_df_cleaned['title'] = movie_df_cleaned['title'].str.title()  # capitalize properly

    # Step 10: Drop duplicates or missing titles
    movie_df_cleaned = movie_df_cleaned.drop_duplicates(subset='title')
    movie_df_cleaned = movie_df_cleaned.dropna(subset=['title'])

    # Step 11: Cleaning values in the genre, writer, actors, and language columns
    movie_df_cleaned["genre"] = movie_df_cleaned["genre"].str.split(",").str[0]
    movie_df_cleaned["writer"] = movie_df_cleaned["writer"].str.split(",").str[0]
    movie_df_cleaned["actors"] = movie_df_cleaned["actors"].str.split(",").str[0]
    movie_df_cleaned["language"] = movie_df_cleaned["language"].str.split(",").str[0]
    return movie_df_cleaned


# 4. Function to visualize movie data
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
    plt.title("Production Budget vs Worldwide Gross", fontsize=14, weight='bold')
    plt.xlabel("Production Budget ($)")
    plt.ylabel("Worldwide Gross ($)")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.show()

    # --- 📈 Top 15 most profitable movies ---
    df["profit"] = df["worldwide_gross"] - df["production_budget"]
    top15 = df.sort_values(by="profit", ascending=False).head(15)

    plt.figure(figsize=(10, 5))
    sns.barplot(
        data=top15,
        x="profit",
        y="title",
        orient="h"
    )
    plt.title("Top 15 most profitable movies 💰", fontsize=14, weight='bold')
    plt.xlabel("Profit ($)")
    plt.ylabel("Movie Title")
    plt.tight_layout()
    plt.show()

# 5. Function to visualize Hypothesis 1 : Low Budget, High IMDb Rating
def visualize_hypothesis_1(df):

    # Drop rows missing either value
    subset = df.dropna(subset=["production_budget", "imdb_rating"])

    # --- Movies with lower production budgets can still achieve high IMDb ratings ---
    plt.scatter(subset["production_budget"], subset["imdb_rating"], alpha=0.7)
    plt.xlabel("IMDb Rating")
    plt.ylabel("Production Budget ($)")
    plt.title("IMDb Rating vs Production Budget")
    plt.grid(True)
    plt.show()

    # Define “low budget” (bottom 25%) & “high rating” (top 25%)
    low_budget = subset["production_budget"].quantile(0.25)
    high_rating = subset["imdb_rating"].quantile(0.75)

    # Pick candidates, then keep Top 10 by rating
    top10 = (subset[(subset["production_budget"] <= low_budget) &
                (subset["imdb_rating"] >= high_rating)]
         .sort_values("imdb_rating", ascending=False)
         .head(10))
    display(top10)

    # Fallback if fewer than 10 found
    if len(top10) < 10:
        top10 = (subset.sort_values(["production_budget", "imdb_rating"],
                                ascending=[True, False])
                    .head(10))

    # ----- Chart: Horizontal bar of ratings -----
    titles = [shorten(str(t), width=22, placeholder="…") for t in top10["title"]]
    ratings = top10["imdb_rating"].tolist()

    plt.figure(figsize=(9,6))
    plt.barh(titles, ratings)
    plt.xlabel("IMDb Rating")
    plt.ylabel("Title")
    plt.title("Top 10 Low-Budget with High IMDb Ratings")
    plt.tight_layout()
    plt.show()

# 6. Function to visualize Hypothesis 2 : Are High IMDB Rated Movies More Profitable?
def visualize_hypothesis_2(df):
    
    # Drop rows missing either value
    subset = df.dropna(subset=["profit", "imdb_rating"])

    # --- 📈 Correlation IMDb Rating ↔ Profit ---
    correlation = subset['imdb_rating'].corr(subset['profit'])
    print(f"📈 Correlation IMDb Rating ↔ Profit : {correlation:.2f}")

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=subset, x='imdb_rating', y='profit', alpha=0.7)
    plt.title("IMDb Rating vs Profit", fontsize=14)
    plt.xlabel("IMDb Rating")
    plt.ylabel("Profit ($)")
    plt.grid(True)
    plt.show()

    # Define “high profit” (top 25%) & “high rating” (top 25%)
    # high_profit = subset["profit"].quantile(0.75)
    high_rating = subset["imdb_rating"].quantile(0.75)

    # Pick candidates, then keep Top 10 by profit
    top10 = (subset[subset["imdb_rating"] >= high_rating]
             .sort_values("profit", ascending=False)
             .head(10))
    display(top10)

    # Fallback if fewer than 10 found
    if len(top10) < 10:
        top10 = (subset.sort_values(["imdb_rating", "profit"],
                                ascending=[False, False])
                    .head(10))

    # ----- Chart: Horizontal bar of profits -----
    titles = [shorten(str(t), width=22, placeholder="…") for t in top10["title"]]
    profits = top10["profit"].tolist()

    plt.figure(figsize=(9,6))
    plt.barh(titles, profits)
    plt.xlabel("Profit ($)")
    plt.ylabel("Title")
    plt.title("Top 10 Most Profitable High IMDb Rated Movies")
    plt.tight_layout()
    plt.show()

# 7. Function to visualize Hypothesis 3 : Some Genres are More Profitable
def visualize_hypothesis_3(movie_df_cleaned):

    # Drop rows missing either value
    subset = movie_df_cleaned.dropna(subset=["production_budget", "worldwide_gross", "imdb_rating", "genre"])

    # --- Return On Investment (ROI) Calculation ---
    subset["profit"] = subset["worldwide_gross"] - subset["production_budget"]
    subset['roi'] = (subset['profit']) / subset['production_budget']

    # Clean ROI data: keep only reasonable values (drop extreme outliers)
    roi_data = subset[(subset['roi'] > -1) & (subset['roi'] < 10)]

    # Group by genre and calculate average ROI and IMDb rating
    genre_stats = roi_data.groupby('genre')[['roi', 'imdb_rating']].mean().sort_values(by='roi', ascending=False)
    genre_stats_profit = subset.groupby('genre')['profit'].mean().sort_values(ascending=False)

    print("📊 Average ROI and IMDb Rating by Genre:")
    display(genre_stats)

    # For the visualization, since we have too many genres, we can plot only the top 10 by ROI
    genre_stats_visualize = genre_stats.head(10)
    plt.figure(figsize=(12, 6))
    sns.barplot(data=genre_stats_visualize.reset_index(), x='genre', y='roi', palette='viridis')
    plt.xticks(rotation=45, ha='right')
    plt.title("Top 10 Average ROI by Movie Genre", fontsize=14)
    plt.xlabel("Genre")
    plt.ylabel("Average ROI")
    plt.show()

    # Display by average profit
    plt.figure(figsize=(12, 6))
    sns.barplot(data=genre_stats_profit.reset_index(), x='genre', y='profit', palette='viridis')
    plt.xticks(rotation=45, ha='right')
    plt.title("Top 10 Average Profit by Movie Genre", fontsize=14)
    plt.xlabel("Genre")
    plt.ylabel("Average Profit")
    plt.show()



   


