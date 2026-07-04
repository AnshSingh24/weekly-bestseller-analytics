import os
import json
import sys
from datetime import date
from app.clean_data import clean_books

# ── Mode detection ────────────────────────────────────────────────────────────
# Set PIPELINE_MODE=live in GitHub Secrets for real runs.
# Locally, leave it unset or set to 'demo' to use mock data.
# This single env var is the only thing separating a credit-spending run
# from a free local test — never change this accidentally.

MODE = os.getenv("PIPELINE_MODE", "demo").lower()

def main():
    print(f"\n{'='*50}")
    print(f"Weekly Bestseller Analytics Dashboard")
    print(f"Date : {date.today()}")
    print(f"Mode : {MODE.upper()}")
    print(f"{'='*50}")

    # ── Step 1: Fetch data ────────────────────────────────────────────────────
    if MODE == "live":
        print("\n[LIVE] Fetching from Rainforest API (costs credits)...")
        from app.fetch_data import fetch_all
        books = fetch_all()
    else:
        print("\n[DEMO] Loading mock data (no credits used)...")
        mock_path = "data/mock/sample_data.json"
        with open(mock_path, "r", encoding="utf-8") as f:
            books = json.load(f)
        # Stamp today's date so snapshots are always current
        for book in books:
            book["snapshot_date"] = str(date.today())
        print(f"  [OK] Loaded {len(books)} books from {mock_path}")

    if not books:
        print("\n[ERROR] No books fetched. Exiting.")
        sys.exit(1)

    print("\n[STEP 2] Cleaning data...")

    # ── Step 2: Clean data ───────────────────────────────────────────────────────
    from app.clean_data import clean_books
    cleaned_books = clean_books(books)

    if not cleaned_books:
        print("\n[ERROR] No valid books after cleaning. Exiting.")
        sys.exit(1)
    
    # ── Step 3: Save to database ──────────────────────────────────────────────
    print("\n[STEP 3] Saving cleaned data to database...")
    from app.db import save_to_db
    save_to_db(books)

    # ── Step 4: Verify analytics ───────────────────────────────────────────────────
    print("\n[STEP 4] Running analytics check...")
    from app.analyze_data import load_data, top_authors, price_stats
    _, snapshot_df = load_data()
    print(f" Top author: {top_authors(snapshot_df).iloc[0]['author']}")
    print(f" Price stats: {price_stats(snapshot_df)}")
    print(f" Total rows: {len(snapshot_df)}")


    print(f"\n{'='*50}")
    print(f"Pipeline complete.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
