import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
   
   db_url = os.environ.get("DATABASE_URL")

   if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
   
   if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

   engine = create_engine(db_url)

   books_df = pd.read_sql("SELECT * FROM books", engine)
    
   snapshot_df = pd.read_sql("""
                              SELECT
                                w.id, w.snapshot_date, w.rank, w.price,
                                w.rating, w.review_count, w.category,
                                b.title, b.author, b.genre, b.asin,
                                b.image_url
                              FROM weekly_snapshot w
                              JOIN books b ON b.id = w.book_id
                              ORDER BY w.snapshot_date, w.rank
                              """, engine)
    
   engine.dispose()

   snapshot_df["snapshot_date"] = pd.to_datetime(snapshot_df["snapshot_date"])
   snapshot_df["price"] = pd.to_numeric(snapshot_df["price"], errors="coerce")
   snapshot_df["rating"] = pd.to_numeric(snapshot_df["rating"], errors="coerce")

   return books_df, snapshot_df

def top_authors(snapshot_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:

    return (snapshot_df.groupby("author")
            .size()
            .reset_index(name="appearances")
            .sort_values("appearances", ascending=False)
            .head(n)
            )

def genre_distribution(snapshot_df: pd.DataFrame) -> pd.DataFrame:


    return (snapshot_df.groupby("genre")["asin"]
            .nunique()
            .reset_index(name="unique_books")
            .sort_values("unique_books", ascending=False)
            )

def price_stats(snapshot_df: pd.DataFrame) -> dict:

    prices = snapshot_df["price"].dropna()
    return {
        "average" : round(prices.mean(), 2),
        "median" : round(prices.median(), 2),
        "cheapest" : round(prices.min(), 2),
        "priciest" : round(prices.max(), 2)
    }

def highest_rated(snapshot_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:

    return (snapshot_df[snapshot_df["review_count"] >= 100]
            .groupby(["asin", "title", "author"])["rating"]
            .mean()
            .reset_index(name="avg_rating")
            .sort_values("avg_rating", ascending=False)
            .head(n)
            )

def rank_history(snapshot_df: pd.DataFrame, asin: str) -> pd.DataFrame:

    return (snapshot_df[snapshot_df["asin"] == asin][["snapshot_date", "rank", "title"]]
            .sort_values("snapshot_date")
            )

def price_history(snapshot_df: pd.DataFrame, asin:str) -> pd.DataFrame:

    return (
        snapshot_df[snapshot_df["asin"] == asin][["snapshot_date", "price", "title"]]
        .sort_values("snapshot_date")
    )

def latest_snapshot(snapshot_df: pd.DataFrame) -> pd.DataFrame:

    latest_date = snapshot_df["snapshot_date"].max()
    return snapshot_df[snapshot_df["snapshot_date"] == latest_date]