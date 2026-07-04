import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ── Connection ────────────────────────────────────────────────────────────────

def get_connection():
    """
    Open and return a connection to Neon PostgreSQL.
    Neon requires sslmode=require — this is already in your connection string,
    but we enforce it here as a safety net.
    """
    if not DATABASE_URL:
        raise EnvironmentError(
            "DATABASE_URL is not set. "
            "Add it to your .env file or GitHub Secrets."
        )
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# ── Core upsert logic ─────────────────────────────────────────────────────────

def upsert_books(conn, books: list[dict]) -> dict:
    """
    Insert books into the 'books' table, skipping duplicates by ASIN.

    Why ON CONFLICT DO NOTHING:
    - ASIN is the natural unique key for a book — same book, same ASIN, always.
    - If a book was inserted in a previous weekly run, we don't touch it again.
    - We only ever UPDATE a book's static info (title, author) if it somehow
      changed — which is rare but possible (e.g. author name correction).

    Returns a dict mapping asin -> book_id for use in snapshot inserts.
    """
    with conn.cursor() as cur:
        for book in books:
            cur.execute("""
                INSERT INTO books (asin, title, author, genre, image_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (asin) DO UPDATE
                    SET title  = EXCLUDED.title,
                        author = EXCLUDED.author
                RETURNING id, asin
            """, (
                book["asin"],
                book["title"],
                book["author"],
                book["genre"],
                book.get("image_url"),
            ))

        conn.commit()

        # Build asin -> id map so snapshot inserts can reference book_id
        cur.execute("SELECT id, asin FROM books")
        return {row[1]: row[0] for row in cur.fetchall()}


def insert_snapshots(conn, books: list[dict], asin_to_id: dict):
    """
    Insert this week's snapshot rows into 'weekly_snapshot'.

    Why ON CONFLICT DO NOTHING here:
    - The UNIQUE constraint on (book_id, snapshot_date, category) means
      if this script runs twice on the same day, the second run is harmless —
      it just skips already-inserted rows instead of creating duplicates.
    - This makes the pipeline idempotent: safe to re-run without side effects.
    """
    rows = []
    skipped = 0

    for book in books:
        book_id = asin_to_id.get(book["asin"])
        if not book_id:
            skipped += 1
            continue

        rows.append((
            book_id,
            book["snapshot_date"],
            book["rank"],
            book["price"],
            book["rating"],
            book["review_count"],
            book["category"],
        ))

    if not rows:
        print("  [WARN] No snapshot rows to insert.")
        return

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO weekly_snapshot
                (book_id, snapshot_date, rank, price, rating, review_count, category)
            VALUES %s
            ON CONFLICT (book_id, snapshot_date, category) DO NOTHING
        """, rows)

    conn.commit()

    if skipped:
        print(f"  [WARN] Skipped {skipped} books with unresolved ASINs.")

    print(f"  [OK] Inserted {len(rows)} snapshot rows into weekly_snapshot.")


# ── Pipeline entry point ──────────────────────────────────────────────────────

def save_to_db(books: list[dict]):
    """
    Full pipeline: connect → upsert books → insert snapshots → close.
    This is the only function called from main.py.
    """
    if not books:
        print("  [WARN] No books to save. Skipping DB write.")
        return

    print(f"\n{'='*50}")
    print(f"Writing {len(books)} books to Neon PostgreSQL")
    print(f"{'='*50}")

    conn = get_connection()

    try:
        print("\n→ Step 1: Upserting books table...")
        asin_to_id = upsert_books(conn, books)
        print(f"  [OK] books table has {len(asin_to_id)} total records.")

        print("\n→ Step 2: Inserting weekly snapshots...")
        insert_snapshots(conn, books, asin_to_id)

    except Exception as e:
        conn.rollback()
        print(f"  [ERROR] DB write failed, rolling back: {e}")
        raise

    finally:
        conn.close()
        print("\n  [OK] DB connection closed.")


# ── Quick connection test ─────────────────────────────────────────────────────

def test_connection():
    """
    Run this to verify your Neon credentials work before running the pipeline.
    Usage: python app/db.py
    """
    print("Testing Neon connection...")
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
    conn.close()
    print(f"  [OK] Connected. Tables found: {tables}")


if __name__ == "__main__":
    test_connection()
