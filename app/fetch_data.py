import os
import json
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# ── Constants ────────────────────────────────────────────────────────────────

API_KEY = os.getenv("RAINFOREST_API_KEY")
BASE_URL = "https://api.rainforestapi.com/request"

# Categories to fetch — each one costs 1 credit.
# Keep this list short to preserve your free tier.
# Current cost: 1 credit per category per weekly run = 4 credits/month per category.
CATEGORIES = [
    {
        "name": "Books",
        "url": "https://www.amazon.in/gp/bestsellers/books",
    },
    {
        "name": "Business & Economics",
        "url": "https://www.amazon.in/gp/bestsellers/books/1318068031",
    },
    {
        "name": "Literature & Fiction",
        "url": "https://www.amazon.in/gp/bestsellers/books/1318157031",
    },
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch_category(category: dict) -> list[dict]:
    """
    Fetch bestsellers for a single category from Rainforest API.
    Returns a list of cleaned book dicts, or empty list on failure.
    """
    params = {
        "api_key": API_KEY,
        "type": "bestsellers",
        "url": category["url"],
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Network error fetching '{category['name']}': {e}")
        return []

    data = response.json()

    # Log credit usage after every request — never let this surprise you.
    req_info = data.get("request_info", {})
    print(f"  [API] Credits used this request : {req_info.get('credits_used_this_request', '?')}")
    print(f"  [API] Credits remaining         : {req_info.get('credits_remaining', '?')}")

    if not req_info.get("success", False):
        print(f"  [ERROR] API returned success=false for '{category['name']}'")
        return []

    raw_books = data.get("bestsellers", [])
    if not raw_books:
        print(f"  [WARN] No bestsellers returned for '{category['name']}'")
        return []

    cleaned = []
    for book in raw_books:
        cleaned.append(parse_book(book, category["name"]))

    print(f"  [OK] Fetched {len(cleaned)} books from '{category['name']}'")
    return cleaned


def parse_book(book: dict, category_name: str) -> dict:
    """
    Extract and normalize fields from a single raw Rainforest book object.

    Notes on tricky fields:
    - 'sub_title.text' is the author, but is absent for some books.
      We fall back to 'Unknown' rather than crashing.
    - 'price' is a nested dict with a 'value' key (numeric, already clean).
      Some books have no price (e.g. free or unavailable) — stored as None.
    - 'rating' and 'ratings_total' can also be absent.
    """
    # Author: lives inside sub_title, which may not exist
    sub_title = book.get("sub_title")
    author = sub_title.get("text", "Unknown") if sub_title else "Unknown"

    # Price: nested dict, value is already a float
    price_obj = book.get("price")
    price = price_obj.get("value") if price_obj else None

    return {
        "asin"          : book.get("asin"),
        "title"         : book.get("title"),
        "author"        : author,
        "genre"         : category_name,
        "image_url"     : book.get("image"),  
        "rank"          : book.get("rank"),
        "price"         : price,
        "rating"        : book.get("rating"),
        "review_count"  : book.get("ratings_total"),
        "category"      : category_name,
        "snapshot_date" : str(date.today()),
    }


def save_raw(data: list[dict], path: str = "data/raw") -> str:
    """
    Save raw results as a JSON snapshot for debugging and audit purposes.
    File is named by today's date so each run produces a unique file.
    """
    os.makedirs(path, exist_ok=True)
    filename = f"{path}/{date.today()}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] Raw snapshot saved to {filename}")
    return filename


# ── Main entry point ─────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    """
    Fetch all configured categories and return a combined list of book dicts.
    This is the function called by the pipeline runner (main.py).
    """
    if not API_KEY:
        raise EnvironmentError(
            "RAINFOREST_API_KEY is not set. "
            "Add it to your .env file or GitHub Secrets."
        )

    print(f"\n{'='*50}")
    print(f"Fetching {len(CATEGORIES)} categories from Rainforest API")
    print(f"{'='*50}")

    all_books = []

    for category in CATEGORIES:
        print(f"\n→ Category: {category['name']}")
        books = fetch_category(category)
        all_books.extend(books)

    print(f"\n{'='*50}")
    print(f"Total books fetched: {len(all_books)}")
    print(f"{'='*50}\n")

    # Save raw snapshot for audit trail
    save_raw(all_books)

    return all_books


if __name__ == "__main__":
    # Run this directly to test: python app/fetch_data.py
    books = fetch_all()
    if books:
        print("Sample entry:")
        print(json.dumps(books[0], indent=2))
