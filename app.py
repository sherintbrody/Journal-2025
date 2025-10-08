import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  # Changed from pytz
import calendar
import json
from pathlib import Path

st.set_page_config(page_title="Trading Notebook", layout="wide")

# --- File Storage Setup ---
DATA_DIR = Path("notebook_data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "notebook_entries.json"

# Initialize data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Helper functions
def get_day_name(date_obj):
    return calendar.day_name[date_obj.weekday()]

def get_ist_timestamp():
    ist = ZoneInfo('Asia/Kolkata')  # Changed from pytz
    return datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p")

def load_entries():
    """Load entries from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_entries(entries):
    """Save entries to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(entries, f, indent=2)

def add_entry(entry):
    """Add a new entry"""
    entries = load_entries()
    # Add unique ID based on timestamp
    entry['id'] = datetime.now().timestamp()
    entries.insert(0, entry)  # Add at beginning for most recent first
    save_entries(entries)

def delete_entry(entry_id):
    """Delete an entry by ID"""
    entries = load_entries()
    entries = [e for e in entries if e.get('id') != entry_id]
    save_entries(entries)

# --- Main App ---
st.title("🗒️ Trading Notebook")
st.markdown("### Your personal trading diary")

# Simple entry form
st.subheader("✍️ Write Entry")

with st.form("notebook_form", clear_on_submit=True):
    # Date and Time
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        date_input = st.date_input("Date", datetime.today())
    
    with col2:
        day_name = get_day_name(date_input)
        st.text_input("Day", value=day_name, disabled=True)
    
    with col3:
        time_input = st.time_input("Time", datetime.now().time())
    
    # News field
    news = st.text_input("📰 News/Events (optional)", placeholder="Any important news or events...")
    
    # Main journal entry
    journal = st.text_area(
        "📝 Journal Entry",
        placeholder="Write your thoughts, observations, trades, lessons learned...",
        height=250
    )
    
    # Save button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True, type="primary")
    
    if submitted:
        if journal or news:
            ist_timestamp = get_ist_timestamp()
            entry = {
                "date": date_input.strftime("%d-%m-%Y"),
                "day": day_name,
                "time": time_input.strftime("%I:%M %p"),
                "news": news,
                "journal": journal,
                "saved_at": ist_timestamp
            }
            
            add_entry(entry)
            st.success(f"✅ Entry saved at {ist_timestamp} IST")
            st.rerun()
        else:
            st.error("Please write something in your journal")

st.divider()

# View entries
st.subheader("📖 Previous Entries")

# Simple filter
view_option = st.selectbox(
    "Show entries from",
    ["All", "Today", "Last 7 Days", "Last 30 Days"],
    index=0
)

# Load all entries
all_entries = load_entries()

# Filter entries based on selection
filtered_entries = []
if view_option == "All":
    filtered_entries = all_entries
elif view_option == "Today":
    today = datetime.now().strftime("%d-%m-%Y")
    filtered_entries = [e for e in all_entries if e.get('date') == today]
elif view_option == "Last 7 Days":
    filtered_entries = all_entries[:20]
elif view_option == "Last 30 Days":
    filtered_entries = all_entries[:50]

# Display entries
if filtered_entries:
    for entry in filtered_entries:
        with st.container():
            st.markdown(f"### 📅 {entry['date']} - {entry['day']} | {entry['time']}")
            
            if entry.get('news'):
                st.info(f"**📰 News:** {entry['news']}")
            
            if entry.get('journal'):
                st.markdown(entry['journal'])
            
            st.caption(f"Saved at: {entry.get('saved_at', 'N/A')} IST")
            
            col1, col2, col3 = st.columns([1, 4, 1])
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{entry.get('id', hash(str(entry)))}"):
                    delete_entry(entry.get('id'))
                    st.success("Entry deleted")
                    st.rerun()
            
            st.divider()
else:
    st.info("📭 No entries yet. Start writing your trading diary!")

# Export option at the bottom
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Export Diary to CSV", use_container_width=True):
        all_entries = load_entries()
        if all_entries:
            df = pd.DataFrame(all_entries)
            if 'id' in df.columns:
                df = df.drop('id', axis=1)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"trading_diary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No entries to export")

with col2:
    if st.button("📥 Export Diary to JSON", use_container_width=True):
        all_entries = load_entries()
        if all_entries:
            export_entries = [{k: v for k, v in entry.items() if k != 'id'} for entry in all_entries]
            json_str = json.dumps(export_entries, indent=2)
            
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"trading_diary_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        else:
            st.info("No entries to export")

with st.expander("ℹ️ Data Storage Info"):
    st.info(f"""
    Your notebook entries are stored locally in: `{DATA_FILE}`
    
    **Note:** 
    - Data is stored in JSON format
    - Entries are automatically saved when you click "Save Entry"
    - You can export your data anytime using the export buttons above
    - The data file persists between app sessions
    """)
