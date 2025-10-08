import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

st.set_page_config(page_title="Trading Journal", layout="wide")



st.title("📒 Trading Journal")

# --- Entry Form ---
with st.form("journal_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        date = st.date_input("Date", datetime.today())
    with c2:
        day = date.strftime("%a")
        st.text_input("Day", value=day, disabled=True)
    with c3:
        time = st.time_input("Time", datetime.now().time())

    news = st.text_input("News (optional)")
    confidence = st.selectbox("Confidence", ["", "Low", "Medium", "High"])
    journal = st.text_area("Journal Notes", height=150)

    submitted = st.form_submit_button("Save Entry")
    if submitted:
        supabase.table("journal").insert({
            "date": str(date),
            "day": day,
            "time": str(time),
            "news": news,
            "confidence": confidence,
            "journal": journal
        }).execute()
        st.success("Journal entry saved ✅")

# --- Load Entries ---
response = supabase.table("journal").select("*").order("date", desc=True).execute()
df = pd.DataFrame(response.data)

if not df.empty:
    st.subheader("📊 Journal Entries")
    st.dataframe(df, use_container_width=True, hide_index=True)
