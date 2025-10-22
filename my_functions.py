# my_functions.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

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