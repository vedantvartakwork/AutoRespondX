import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from datetime import datetime

st.set_page_config(
    page_title="AutoRespondX Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Auto refresh every 5 seconds
st.markdown(
    """
    <meta http-equiv="refresh" content="10">
    """,
    unsafe_allow_html=True
)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autorespond",
    "user": "postgres",
    "password": "password"
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@st.cache_data(ttl=5)
def load_data():
    conn = get_connection()

    processed_df = pd.read_sql("""
        SELECT 
            id,
            hashed_user_id,
            predicted_label,
            is_duplicate
        FROM processed_tweets
        ORDER BY id DESC
    """, conn)

    reply_df = pd.read_sql("""
        SELECT 
            reply_text,
            reply_status
        FROM reply_outbox
    """, conn)

    try:
        metrics_df = pd.read_sql("""
            SELECT *
            FROM metrics
        """, conn)
    except Exception:
        metrics_df = pd.DataFrame()

    conn.close()

    processed_tweets = len(processed_df)
    replies_queued = len(reply_df)
    metrics_logged = len(metrics_df) if not metrics_df.empty else processed_tweets + replies_queued

    if not processed_df.empty:
        label_data = (
            processed_df["predicted_label"]
            .fillna("unknown")
            .str.title()
            .value_counts()
            .reset_index()
        )
        label_data.columns = ["Label", "Count"]
    else:
        label_data = pd.DataFrame({
            "Label": ["Inquiry", "Complaint", "Praise"],
            "Count": [0, 0, 0]
        })

    duplicate_count = int(processed_df["is_duplicate"].sum()) if not processed_df.empty else 0
    non_duplicate_count = processed_tweets - duplicate_count

    duplicate_data = pd.DataFrame({
        "Type": ["Duplicate", "Non-Duplicate"],
        "Count": [duplicate_count, non_duplicate_count]
    })

    recent_processed = processed_df.head(10).copy()

    if not recent_processed.empty:
        recent_processed = recent_processed.rename(columns={
            "id": "ID",
            "hashed_user_id": "Hashed User ID",
            "predicted_label": "Label",
            "is_duplicate": "Is Duplicate"
        })

        recent_processed["Status"] = recent_processed["Is Duplicate"].apply(
            lambda x: "duplicate" if x else "normal"
        )

        recent_processed = recent_processed[
            ["ID", "Hashed User ID", "Label", "Status"]
        ]
    else:
        recent_processed = pd.DataFrame(columns=["ID", "Hashed User ID", "Label", "Status"])

    complaint_count = 0
    if not processed_df.empty:
        complaint_count = int(
            processed_df["predicted_label"]
            .fillna("")
            .str.lower()
            .eq("complaint")
            .sum()
        )

    complaint_status = "ALERT TRIGGERED" if complaint_count >= 5 else "NORMAL"

    return {
        "processed_tweets": processed_tweets,
        "replies_queued": replies_queued,
        "metrics_logged": metrics_logged,
        "label_data": label_data,
        "duplicate_data": duplicate_data,
        "recent_processed": recent_processed,
        "complaint_count": complaint_count,
        "complaint_status": complaint_status
    }


try:
    data = load_data()
    db_status = "CONNECTED"
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()


processed_tweets = data["processed_tweets"]
replies_queued = data["replies_queued"]
metrics_logged = data["metrics_logged"]
label_data = data["label_data"]
duplicate_data = data["duplicate_data"]
recent_processed = data["recent_processed"]
complaint_count = data["complaint_count"]
complaint_status = data["complaint_status"]

total_duplicates = int(duplicate_data.loc[duplicate_data["Type"] == "Duplicate", "Count"].sum())

if not label_data.empty:
    top_category = label_data.sort_values("Count", ascending=False).iloc[0]["Label"]
else:
    top_category = "N/A"

last_updated = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

label_rows_html = "".join(
    f'<div class="mini-line">{row["Label"]}: <b>{row["Count"]}</b></div>'
    for _, row in label_data.iterrows()
)

duplicate_rows_html = "".join(
    f'<div class="mini-line">{row["Type"]}: <b>{row["Count"]}</b></div>'
    for _, row in duplicate_data.iterrows()
)
duplicate_rows_html += f'<div class="mini-line">Total Flagged: <b>{total_duplicates}</b></div>'

st.markdown("""
<style>
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"]  { display: none !important; }
    [data-testid="stToolbar"]         { display: none !important; }
    .stAppDeployButton                { display: none !important; }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 0.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 1500px;
    }

    h1, h2, h3 { margin-top: 0; margin-bottom: 0.4rem; }

    .dashboard-title {
        font-size: 32px;
        font-weight: 850;
        color: #111827;
        margin-bottom: 0;
    }

    .dashboard-subtitle {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 10px;
    }

    .run-label {
        display: inline-block;
        background-color: #eef2ff;
        color: #3730a3;
        padding: 7px 14px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .metric-card {
        background: white;
        padding: 18px 20px;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        border: 1px solid #eef2f7;
        height: 118px;
    }

    .metric-label {
        font-size: 14px;
        color: #6b7280;
        font-weight: 700;
    }

    .metric-value {
        font-size: 38px;
        color: #111827;
        font-weight: 850;
        line-height: 1.1;
        margin-top: 8px;
    }

    .mini-card {
        background: white;
        padding: 15px 17px;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        border: 1px solid #eef2f7;
        height: 140px;
    }

    .alert-card {
        background: #fff7ed;
        padding: 15px 17px;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.07);
        border: 1px solid #fed7aa;
        height: 140px;
    }

    .mini-title {
        font-size: 15px;
        color: #374151;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .mini-line {
        font-size: 14px;
        color: #111827;
        margin-bottom: 5px;
    }

    .alert-badge {
        display: inline-block;
        background: #dc2626;
        color: white;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 850;
        margin-top: 5px;
    }

    .health-badge {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
    }

    .insight-card {
        background: #ffffff;
        padding: 12px 15px;
        border-radius: 16px;
        border: 1px solid #eef2f7;
        box-shadow: 0 3px 12px rgba(0,0,0,0.06);
        height: 85px;
    }

    .insight-label {
        font-size: 13px;
        color: #6b7280;
        font-weight: 700;
    }

    .insight-value {
        font-size: 21px;
        color: #111827;
        font-weight: 850;
        margin-top: 4px;
    }

    div[data-testid="stDataFrame"] {
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="dashboard-title">AutoRespondX Real-Time Analytics Dashboard</div>
<div class="dashboard-subtitle">
    Live PostgreSQL Source | AutoRespondX | Last Updated: {last_updated}
</div>
<div class="run-label">
    Serving Layer Dashboard • Processed Tweets • Reply Queue • Metrics • Duplicate Detection • Complaint Spike
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Processed Tweets</div>
        <div class="metric-value">{processed_tweets}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Replies Queued</div>
        <div class="metric-value">{replies_queued}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Metrics Logged</div>
        <div class="metric-value">{metrics_logged}</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Duplicate Flags</div>
        <div class="metric-value">{total_duplicates}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown(f"""
    <div class="mini-card">
        <div class="mini-title">Label Distribution</div>
        {label_rows_html}
    </div>
    """, unsafe_allow_html=True)

with s2:
    st.markdown(f"""
    <div class="mini-card">
        <div class="mini-title">Duplicate Summary</div>
        {duplicate_rows_html}
    </div>
    """, unsafe_allow_html=True)

with s3:
    st.markdown(f"""
    <div class="alert-card">
        <div class="mini-title">Complaint Spike</div>
        <div class="mini-line">Total Complaints: <b>{complaint_count}</b></div>
        <div class="alert-badge">{complaint_status}</div>
    </div>
    """, unsafe_allow_html=True)

with s4:
    st.markdown(f"""
    <div class="mini-card">
        <div class="mini-title">Pipeline Health</div>
        <div class="mini-line">Pipeline Status: <span class="health-badge">RUNNING</span></div>
        <div class="mini-line">Database: <b>PostgreSQL</b></div>
        <div class="mini-line">DB Status: <b>{db_status}</b></div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.1, 1.1, 1.8])

with c1:
    st.subheader("Class Distribution")
    fig1 = px.bar(label_data, x="Label", y="Count", text="Count")
    fig1.update_traces(textposition="outside")
    fig1.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis_title=None,
        yaxis_title=None
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.subheader("Duplicate Tracking")
    fig2 = px.bar(duplicate_data, x="Type", y="Count", text="Count")
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=20),
        xaxis_title=None,
        yaxis_title=None
    )
    st.plotly_chart(fig2, use_container_width=True)

with c3:
    st.subheader("Recent Processed Tweets")

    styled_table = recent_processed.style.applymap(
        lambda v: (
            "background-color: #dbeafe; color: #1e40af; font-weight: 700;" if str(v).lower() == "inquiry"
            else "background-color: #ffedd5; color: #9a3412; font-weight: 700;" if str(v).lower() == "complaint"
            else "background-color: #dcfce7; color: #166534; font-weight: 700;" if str(v).lower() == "praise"
            else "background-color: #fee2e2; color: #991b1b; font-weight: 700;" if str(v).lower() == "duplicate"
            else "background-color: #f3f4f6; color: #374151; font-weight: 700;" if str(v).lower() == "normal"
            else ""
        )
    )

    st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True,
        height=285
    )

i1, i2, i3 = st.columns(3)

with i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-label">Top Category</div>
        <div class="insight-value">{top_category}</div>
    </div>
    """, unsafe_allow_html=True)

with i2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-label">Complaint Spike</div>
        <div class="insight-value">{complaint_status}</div>
    </div>
    """, unsafe_allow_html=True)

with i3:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-label">Duplicate Detection</div>
        <div class="insight-value">{total_duplicates} Total Flagged</div>
    </div>
    """, unsafe_allow_html=True)