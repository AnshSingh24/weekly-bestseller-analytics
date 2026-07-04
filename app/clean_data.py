import pandas as pd

def clean_books(books: list[dict]) -> list[dict]:
    """
    Takes raw book dicts from fetch_data (or mock),
    cleans them with pandas, returns cleaned list of dicts.
    """

    if not books:
        return []
    
    df = pd.DataFrame(books)

    print(f"\n{'='*50}")
    print(f"Cleaning {len(df)} raw records...")
    print(f"{'='*50}")

    original_count = len(df)

    df.dropna(subset=["asin", "title"], inplace=True)

    df.sort_values("rank", inplace=True)
    df.drop_duplicates(subset=["asin", "category", "snapshot_date"],
                       keep="first", inplace=True)
    
    df["title"] = df["title"].str.strip()
    df["author"] = df["author"].str.strip()

    df["author"] = df["author"].replace("", "Unknown")
    df.loc[df["author"].str.strip() == "", "author"] = "Unknown"

    df.loc[df["price"]<0, "price"] = None

    df.loc[~df["rating"].between(1.0, 5.0, inclusive="both"), "rating"] = None

    df.loc[df["review_count"]<0, "review_count"] = None

    df.loc[df["rank"]<1,"rank"]=None

    df["rank"] = df["rank"].astype("Int64")
    df["review_count"] = df["review_count"].astype("Int64")
    df["price"] = df["price"].astype(float)

    dropped = original_count - len(df)
    print(f" [OK] Cleaned. Dropped {dropped} invalid rows, {len(df)} remain.")

    return df.to_dict(orient="records")