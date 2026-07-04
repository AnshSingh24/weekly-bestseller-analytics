# 📚 Weekly Bestseller Analytics Dashboard

A cloud-based data pipeline that automatically tracks Amazon India's bestselling books 
every week, stores historical snapshots in PostgreSQL, and displays trends through an 
interactive analytics dashboard.

🔗 **[Live Dashboard](https://weekly-bestseller-analytics.streamlit.app/)** 

---

## 🧠 What Problem Does This Solve?

Most Amazon bestseller projects use static, outdated CSV datasets and can't answer:
- Which books are trending *right now*?
- How has a book's price changed over the past months?
- Which authors consistently dominate the rankings?
- Which genres are growing in popularity?

This project solves that by building an automated pipeline that collects and stores 
fresh data every week — enabling genuine trend analysis over time.

---

## 🏗️ Architecture

```text
GitHub Actions (Every Sunday)
           ↓
Rainforest API (Amazon Bestsellers)
           ↓
Data Cleaning (Pandas)
           ↓
Neon PostgreSQL (Historical Storage)
           ↑
Streamlit Dashboard (Live Analytics)
```

---

## ✨ Features

- **Automated weekly pipeline** — runs every Sunday via GitHub Actions, zero manual intervention
- **Historical tracking** — stores weekly snapshots so trends emerge over time
- **Interactive dashboard** with 4 tabs:
  - 🏆 Overview — this week's top books with cover images
  - ✍️ Authors — most dominant authors and highest rated books
  - 💰 Prices & Ratings — distributions, statistics, price vs rating scatter
  - 🔍 Book Detail — rank and price history charts for any individual book
- **Cost-optimized design** — pipeline and dashboard are fully decoupled; visitor traffic costs zero API credits
- **Idempotent upserts** — safe to re-run without creating duplicate data

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Scheduling | GitHub Actions (cron) |
| Data Collection | Rainforest API |
| Data Cleaning | Pandas |
| Database | Neon PostgreSQL |
| Dashboard | Streamlit + Plotly |
| Language | Python 3.11 |

---

## 📊 Database Schema

```sql
-- Static book identity
books (id, asin, title, author, genre, image_url, first_seen_at)

-- Weekly time-series data
weekly_snapshot (id, book_id, snapshot_date, rank, price, rating, review_count, category)
```

The two-table design separates static book data from time-varying metrics — enabling 
efficient historical queries without data duplication.

---

## 🚀 Running Locally

**1. Clone and set up environment:**
```bash
git clone https://github.com/your-username/weekly-bestseller-analytics
cd weekly-bestseller-analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create `.env` file:**

RAINFOREST_API_KEY=your_key_here
DATABASE_URL=your_neon_connection_string

**3. Run in demo mode (no API credits used):**
```bash
python main.py
```

**4. Launch dashboard:**
```bash
streamlit run streamlit_app/dashboard.py
```

---

## ⚙️ Pipeline Modes

| Mode | Command | API Credits |
|---|---|---|
| Demo (local dev) | `python main.py` | 0 |
| Live (production) | `PIPELINE_MODE=live python main.py` | 2 per run |

All local development uses mock data by default — live API calls are reserved 
for confirmed-working production runs only.

---

## 💡 Key Engineering Decisions

**Weekly sampling over daily:** Bestseller rankings have low daily volatility — 
a book ranked #1 on Tuesday is typically still #1 on Thursday. Weekly sampling 
preserves meaningful trend signal while reducing API cost by 7x.

**Pipeline/dashboard decoupling:** The Streamlit dashboard reads exclusively from 
Neon PostgreSQL. Visitor traffic generates zero API calls — 1 visitor or 10,000 
visitors costs the same: nothing.

**Idempotent design:** The `ON CONFLICT DO NOTHING` constraint on 
`(book_id, snapshot_date, category)` means the pipeline can be re-run safely 
without creating duplicate snapshot rows.

---

## 📈 Skills Demonstrated

- Data Engineering & ETL Pipeline Design
- PostgreSQL Schema Design & Query Optimization
- REST API Integration & Cost Optimization
- Automated Scheduling with GitHub Actions
- Data Visualization with Plotly
- Streamlit Dashboard Development
- Python (Pandas, psycopg2, SQLAlchemy)

---

## 🔮 Future Enhancements

- [ ] Price drop email alerts
- [ ] ML-based rank prediction
- [ ] Expand to multiple Amazon categories
- [ ] Sentiment analysis on book reviews
- [ ] Docker containerization

---

## ⚠️ Note on Data

This project uses the Rainforest API, a licensed third-party service for 
Amazon data. No direct scraping of Amazon is performed.

---

*Built by [Ansh Singh](https://github.com/AnshSingh24) · 2026*
