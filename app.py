import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import calendar
import json
from pathlib import Path
from collections import defaultdict
import re

st.set_page_config(page_title="Trading Notebook", layout="wide")

# --- File Storage Setup ---
DATA_DIR = Path("notebook_data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "notebook_entries.json"

# Initialize data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# Initialize session state
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

# Helper functions
def get_day_name(date_obj):
    return calendar.day_name[date_obj.weekday()]

def get_ist_time():
    """Get current time in IST"""
    ist = ZoneInfo('Asia/Kolkata')
    return datetime.now(ist)

def get_ist_timestamp():
    ist = ZoneInfo('Asia/Kolkata')
    return datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p")

def format_journal_text(text):
    """Format journal text: each sentence on a new line"""
    if not text:
        return ""
    
    # Split by sentence endings (., !, ?) followed by space or end of string
    # This regex keeps the punctuation with the sentence
    sentences = re.split(r'([.!?]+(?:\s+|$))', text)
    
    # Combine sentences with their punctuation and add line breaks
    formatted_lines = []
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i].strip()
        punctuation = sentences[i+1].strip() if i+1 < len(sentences) else ''
        if sentence:
            formatted_lines.append(sentence + punctuation)
    
    # Handle last sentence if no punctuation
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        formatted_lines.append(sentences[-1].strip())
    
    # Join with line breaks
    return '<br>'.join(formatted_lines)

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
    entry['id'] = datetime.now().timestamp()
    entries.insert(0, entry)
    save_entries(entries)

def delete_entry(entry_id):
    """Delete an entry by ID"""
    entries = load_entries()
    entries = [e for e in entries if e.get('id') != entry_id]
    save_entries(entries)

def group_entries_by_date(entries):
    """Group entries by date, maintaining order"""
    grouped = defaultdict(list)
    date_order = []  # To maintain order of dates
    
    for entry in entries:
        date = entry.get('date')
        if date not in date_order:
            date_order.append(date)
        grouped[date].append(entry)
    
    return grouped, date_order

def get_dates_with_entries():
    """Get all unique dates that have entries"""
    all_entries = load_entries()
    dates = set()
    for entry in all_entries:
        dates.add(entry.get('date'))
    return dates

# Custom CSS for compact boxes
st.markdown("""
<style>
    .entry-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 15px;
    }
    .dark-mode .entry-box {
        background-color: #262730;
        border-left: 4px solid #58a6ff;
    }
    .entry-time {
        color: #1f77b4;
        font-weight: bold;
        font-size: 1.1em;
    }
    .entry-content {
        margin-top: 10px;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)

# --- Main App ---
st.title("🗒️ Trading Notebook")
st.markdown("### Your personal trading diary")

# Simple entry form
st.subheader("✍️ Write Entry")

# Use form_key to force form reset
with st.form(f"notebook_form_{st.session_state.form_key}", clear_on_submit=True):
    # Date and Time
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Get IST date
        ist_now = get_ist_time()
        date_input = st.date_input("Date", ist_now.date())
    
    with col2:
        day_name = get_day_name(date_input)
        st.text_input("Day", value=day_name, disabled=True)
    
    with col3:
        # Get current IST time
        current_ist_time = get_ist_time().time()
        time_input = st.time_input("Time (IST)", current_ist_time)
    
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
                "time": time_input.strftime("%I:%M %p"),  # 12-hour format
                "news": news,
                "journal": journal,
                "saved_at": ist_timestamp
            }
            
            add_entry(entry)
            st.success(f"✅ Entry saved at {ist_timestamp} IST")
            # Increment form key to reset form with new time
            st.session_state.form_key += 1
            st.rerun()
        else:
            st.error("Please write something in your journal")

st.divider()

# View entries
st.subheader("📖 Previous Entries")

# View options with tabs
tab1, tab2 = st.tabs(["📅 Calendar View", "📋 List View"])

# Load all entries
all_entries = load_entries()

with tab1:
    st.markdown("#### Select a date to view entries")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Calendar date picker
        selected_date = st.date_input(
            "Pick a date",
            get_ist_time().date(),
            key="calendar_picker"
        )
    
    with col2:
        # Show available dates
        dates_with_entries = get_dates_with_entries()
        if dates_with_entries:
            st.info(f"📊 You have entries on {len(dates_with_entries)} different days")
    
    # Filter entries for selected date
    selected_date_str = selected_date.strftime("%d-%m-%Y")
    calendar_filtered = [e for e in all_entries if e.get('date') == selected_date_str]
    
    st.markdown("---")
    
    if calendar_filtered:
        day_name = get_day_name(selected_date)
        st.markdown(f"### 📅 {selected_date_str} - {day_name}")
        st.caption(f"💭 {len(calendar_filtered)} {'entry' if len(calendar_filtered) == 1 else 'entries'} on this day")
        
        # Display entries in compact boxes
        for idx, entry in enumerate(calendar_filtered, 1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                with st.container():
                    st.markdown(f"""
                    <div class="entry-box">
                        <div class="entry-time">⏰ {entry['time']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if entry.get('news'):
                        st.info(f"**📰 News:** {entry['news']}")
                    
                    if entry.get('journal'):
                        formatted_journal = format_journal_text(entry['journal'])
                        st.markdown(f"<div class='entry-content'>{formatted_journal}</div>", unsafe_allow_html=True)
                    
                    st.caption(f"📝 Saved at: {entry.get('saved_at', 'N/A')} IST")
            
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("🗑️ Delete", key=f"cal_delete_{entry.get('id')}", use_container_width=True):
                    delete_entry(entry.get('id'))
                    st.success("Entry deleted")
                    st.rerun()
            
            if idx < len(calendar_filtered):
                st.markdown("---")
    else:
        st.info(f"📭 No entries found for {selected_date_str}")

with tab2:
    # Simple filter
    view_option = st.selectbox(
        "Show entries from",
        ["All", "Today", "Last 7 Days", "Last 30 Days"],
        index=0
    )
    
    # Filter entries based on selection
    filtered_entries = []
    if view_option == "All":
        filtered_entries = all_entries
    elif view_option == "Today":
        today = get_ist_time().strftime("%d-%m-%Y")
        filtered_entries = [e for e in all_entries if e.get('date') == today]
    elif view_option == "Last 7 Days":
        filtered_entries = all_entries[:20]
    elif view_option == "Last 30 Days":
        filtered_entries = all_entries[:50]
    
    st.markdown("---")
    
    # Display entries grouped by date in compact format
    if filtered_entries:
        grouped_entries, date_order = group_entries_by_date(filtered_entries)
        
        for date in date_order:
            entries_for_date = grouped_entries[date]
            entry_count = len(entries_for_date)
            day_name = entries_for_date[0].get('day', '')
            
            st.markdown(f"### 📅 {date} - {day_name}")
            st.caption(f"💭 {entry_count} {'entry' if entry_count == 1 else 'entries'} on this day")
            
            # Display entries in two columns for compact view
            for idx, entry in enumerate(entries_for_date):
                # Use columns for compact display
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Compact box for each entry
                    with st.container():
                        st.markdown(f"""
                        <div class="entry-box">
                            <div class="entry-time">⏰ {entry['time']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if entry.get('news'):
                            st.info(f"**📰 News:** {entry['news']}")
                        
                        if entry.get('journal'):
                            formatted_journal = format_journal_text(entry['journal'])
                            st.markdown(f"<div class='entry-content'>{formatted_journal}</div>", unsafe_allow_html=True)
                        
                        st.caption(f"📝 Saved at: {entry.get('saved_at', 'N/A')} IST")
                
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button("🗑️ Delete", key=f"list_delete_{entry.get('id')}", use_container_width=True):
                        delete_entry(entry.get('id'))
                        st.success("Entry deleted")
                        st.rerun()
                
                if idx < len(entries_for_date) - 1:
                    st.markdown("---")
            
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
    - All times are in IST (Indian Standard Time)
    - Each sentence in your journal will appear on a new line for better readability
    - Entries are grouped by date for easy viewing
    - Use Calendar View to see entries for specific dates
    - Use List View to browse all entries chronologically
    - Entries are automatically saved when you click "Save Entry"
    - You can export your data anytime using the export buttons above
    - The data file persists between app sessions
    - Times are displayed in 12-hour format (AM/PM)
    """)
