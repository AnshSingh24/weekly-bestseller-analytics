import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

def display_book_image(image_url: str, width: int =120):
    
    if not image_url:
        st.markdown("📚")
        return
    
    # clean_url = image_url.replace("https://", "").replace("https://", "")
    proxy_url = f"https://wsrv.nl/?url={image_url}&w={width}&output=jpg"
    
    st.markdown(
        f'<img src="{proxy_url}" width="{width}" '
        f'style="border-radius:8px; object-fit:cover;" '
        f'onerror="this.styledisply=\'none\'">',
        unsafe_allow_html=True
    )

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analyze_data import (
    highest_rated,
    latest_snapshot,
    load_data,
    price_history,
    price_stats,
    rank_history,
    top_authors,
    genre_distribution,
)


st.set_page_config(
    page_title="Weekly Bestseller Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0e1117; color: #fafafa;}
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1c1f26;
        border: 1px solid #2d3139;
        border-radius: 10px;
        padding: 16px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1c1f26;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a0aec0;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2d3748;
        color: #fafafa;
    }
    
    /* Selectbox */
    .stSelectbox > div >div {
        background-color: #1c1f26;
        border: 1px solid #2d3139;
    }
    
    /* Divider */
    hr { border-color: #2d3139; }
    
    /* Header */
    .dashboard-header {
        padding: 20px 0 10px 0;
        border-bottom: 1px solid #2d3139;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

PLOT_THEME = {
    "template": "plotly_dark",
    "paper_bgcolor": "#1c1f26",
    "plot_bgcolor": "#1c1f26",
}


@st.cache_data(ttl=3600)
def get_data():
    return load_data()


st.markdown('<div class="dashboard-header">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("## 📚 Weekly Bestseller Ananlytics Dashboard")
    st.markdown("Amazon India . Books . Updated Weekly")
with col2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
st.markdown('</div', unsafe_allow_html=True)


with st.spinner("Loading data from database..."):
    try:
        books_df, snapshot_df = get_data()
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()
        
latest_df = latest_snapshot(snapshot_df)


st.markdown("### This Week at a Glance")
m1, m2, m3, m4, m5 =st.columns(5)

stats = price_stats(snapshot_df)

m1.metric("📖 Books Tracked",   len(books_df))
m2.metric("📸 Total Snapshots", len(snapshot_df))
m3.metric("💰 Avg Price",       f"₹{stats['average']}")
m4.metric("⭐ Top Rating",      f"{snapshot_df['rating'].max()}")
m5.metric("✍️ Unique Authors",  snapshot_df['author'].nunique())

st.markdown("---")


tab1, tab2, tab3, tab4 =st.tabs([
    "🏆 Overview",
    "✍️ Authors",
    "💰 Prices & Ratings",
    "🔍 Book Detail",
])

# ______________________________________________________________________________
# TAB 1 — OVERVIEW
# ______________________________________________________________________________

with tab1:
    st.markdown("### This Week's top Books")
    
    
top_books = latest_df.sort_values("rank").reset_index(drop=True)

# st.write(top_books[["title", "image_url"]].head())

for i in range(0, len(top_books), 3):
    row_books = top_books.iloc[i:i+3]
    cols = st.columns(3)
    for col, (_, book) in zip(cols, row_books.iterrows()):
        with col:
            if book.get("image_url"):
                display_book_image(book["image_url"], width=120)
            st.markdown(f"**#{int(book['rank'])} {book['title'][:50]}**")
            st.markdown(f"*{book['author']}*")
            st.markdown(f"₹{book['price']} . ⭐ {book['rating']}")
            st.markdown("---")

st.markdown("---")
st.markdown("### Genre Distribution")

genre_df = genre_distribution(snapshot_df)
fig_genre = px.pie(
    genre_df,
    names="genre",
    values="unique_books",
    hole=0.45,
    color_discrete_sequence=px.colors.sequential.Plasma_r,
)
fig_genre.update_layout(
    **PLOT_THEME,
    legend=dict(orientation="v", x=1, y=0.5),
    margin=dict(t=20, b=20),
)
fig_genre.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig_genre, use_container_width=True)

#________________________________________________________________________________
# TAB 2 - AUTHORS
#________________________________________________________________________________


with tab2:
    st.markdown("### Top Authors by Appearances")
    st.caption("Counts total weekly appearances - reflects sustained presence on the list")
    
    n = st.slider("Show top N authors", min_value=5, max_value=20, value=10)
    authors_df = top_authors(snapshot_df, n=n)
    
    authors_df = authors_df[authors_df["author"] != "Unknown"]
    
    fig_authors = px.bar(
        authors_df.sort_values("appearances"),
        x="appearances",
        y="author",
        orientation="h",
        color="appearances",
        labels={"appaerances": "Appearances", "author": ""},
    )
    fig_authors.update_layout(
        **PLOT_THEME,
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(t=10, b=10),
        yaxis=dict(tickfont=dict(size=13)),
    )
    st.plotly_chart(fig_authors, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### Highest Rated Books")
    st.caption("Minimum 100 reviews to qualify -  avoids books with inflated ratings from few reviews.")
    
    rated_df = highest_rated(snapshot_df)
    fig_rated = px.bar(
        rated_df.sort_values("avg_rating"),
        x="avg_rating",
        y="title",
        orientation="h",
        color="avg_rating",
        color_continuous_scale="Teal",
        labels={"avg_rating": "Avg rating", "title": ""},
        range_x=[3.5, 5.0],
    )
    fig_rated.update_layout(
        **PLOT_THEME,
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(t=10, b=10),
        yaxis=dict(tickfont=dict(size=12)),
    )
    st.plotly_chart(fig_rated, use_container_width=True)
    
    #_____________________________________________________________________________________________________________
    #TAB 3 - PRICES & RATINGS
    #_____________________________________________________________________________________________________________
    
    with tab3:
        st.markdown("### Price Statistics")
        
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Average Price",  f"₹{stats['average']}")
        p2.metric("Median Price",   f"₹{stats['median']}")
        p3.metric("Cheapest Book",  f"₹{stats['cheapest']}")
        p4.metric("Priciest Book",  f"₹{stats['priciest']}")
        
        st.markdown("---")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### Price Distribution")
            fig_price = px.histogram(
                snapshot_df.dropna(subset=["price"]),
                x="price",
                nbins=20,
                color_discrete_sequence=["#7c3aed"],
                labels={"price": "Price (₹)", "count": "Books"},
            )
            fig_price.update_layout(**PLOT_THEME, margin=dict(t=10, b=10))
            st.plotly_chart(fig_price, use_container_width=True)
            
        with col_b:
            st.markdown("### Rating Distribution")
            fig_rating = px.histogram(
                snapshot_df.dropna(subset=["rating"]),
                x="rating",
                nbins=10,
                color_discrete_sequence=["#0891b2"],
                labels={"rating": "Rating", "count": "Books"},
                range_x=[1, 5],
            )
            fig_rating.update_layout(**PLOT_THEME, margin=dict(t=10, b=10))
            st.plotly_chart(fig_rating, use_container_width=True)
            
        st.markdown("---")
        st.markdown("### Price vs Rating")
        st.caption("Does a higher price mean a better book?")
        
        fig_scatter = px.scatter(
            snapshot_df.dropna(subset=["price", "rating"]),
            x="price",
            y="rating",
            hover_name="title",
            hover_data=["author", "category"],
            color_discrete_sequence=px.colors.qualitative.Vivid,
            labels={"price": "Price (₹)", "rating": "Rating"},
        )
        fig_scatter.update_layout(**PLOT_THEME, margin=dict(t=10, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
#______________________________________________________________________________________
#TAB 4 - BOOK DETAIL DRILL-DOWN
#______________________________________________________________________________________


with tab4:
    st.markdown("### Book Detail View")
    st.caption("Select a book to see its rank and price history over time.")
    
    book_options = books_df.apply(
        lambda r: f"{r['title'][:60]} - {r['author']}", axis=1
    ).tolist()
    asin_list = books_df["asin"].tolist()
    
    selected_label = st.selectbox("Choose a book", book_options)
    selected_idx = book_options.index(selected_label)
    selected_asin = asin_list[selected_idx]
    
    rank_df = rank_history(snapshot_df, selected_asin)
    price_df = price_history(snapshot_df, selected_asin)
    
    if len(rank_df) < 2:
        st.info("This book only has one week of data so far - check back after the next pipeline run to see trend lines.")
        
    
book_row = books_df[books_df["asin"] == selected_asin].iloc[0]
snap_row = snapshot_df[snapshot_df["asin"] == selected_asin].iloc[-1]


detail_left, detail_right = st.columns([1, 3])

with detail_left:
    if book_row.get("image_url"):
        display_book_image(book_row["image_url"], width=160)
    else:
        st.markdown("📚 NO cover available")
        
with detail_right:
    info_cols = st.columns(4)
    info_cols[0].metric("Current Rank", f"#{int(snap_row['rank'])}" if snap_row['rank'] else "N/A")
    info_cols[1].metric("Current Price", f"₹{snap_row['price']}" if snap_row['price'] else "N/A")
    info_cols[2].metric("Rating", f"⭐ {snap_row['rating']}" if snap_row['rating'] else "N/A")
    info_cols[3].metric("Total Reviews", f"{int(snap_row['review_count']):,}" if snap_row['review_count'] else "N/A")


st.markdown("---")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Rank History")
    st.caption("Lower = better position")
    fig_rank = go.Figure()
    fig_rank.add_trace(go.Scatter(
        x=rank_df["snapshot_date"],
        y=rank_df["rank"],
        mode="lines+markers",
        line=dict(color="#7c3aed", width=2),
        marker=dict(size=8),
        name="Rank",
    ))
    fig_rank.update_yaxes(autorange="reversed")
    fig_rank.update_layout(
        **PLOT_THEME,
        xaxis_title="Date",
        yaxis_title="Rank",
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_rank, use_container_width=True)
    
with chart_col2:
    st.markdown("#### Price History")
    fig_price_hist = go.Figure()
    fig_price_hist.add_trace(go.Scatter(
        x=price_df["snapshot_date"],
        y=price_df["price"],
        mode="lines+markers",
        line=dict(color="#0891b2", width=2),
        marker=dict(size=8),
        name="Price (₹)",
        fill="tozeroy",
        fillcolor="rgba(8,145,178,0.1)",
    ))
    fig_price_hist.update_layout(
        **PLOT_THEME,
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_price_hist, use_container_width=True)
