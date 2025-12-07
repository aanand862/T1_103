import streamlit as st
import datetime
import calendar
from data_handler import save_entry, load_data

# Page config
st.set_page_config(
    page_title="T1-103 Utilities APP",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for calendar buttons
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 60px;
        font-weight: bold;
        border: 1px solid #ddd;
    }
    .today-btn {
        border: 2px solid #4CAF50 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("T1-103 Utilities APP 🏠")

# Sidebar navigation
page = st.sidebar.radio("Navigate", ["Milk 🥛", "Maid 🧹", "Cook 🍳"], horizontal=True)

# Helper to determining status icon
def get_status_icon(log_type, date_obj, data_df):
    if data_df.empty:
        return "❔"
    
    # Filter for this date
    # data_df 'date' is already datetime.date objects from load_data
    row = data_df[data_df['date'] == date_obj]
    
    if row.empty:
        # If it's today or future, maybe neutral? If past, question mark?
        if date_obj < datetime.date.today():
             return "⚠️" # Missing past log
        return "❔"

    row = row.iloc[0]
    
    if log_type == "Milk 🥛":
        return f"({row['quantity']}L)" if row['delivered'] else "❌"
    elif log_type == "Maid 🧹":
        # M = Morning, E = Evening
        m = "✅" if row['morning_status'] == 'Present' else "❌"
        e = "✅" if row['evening_status'] == 'Present' else "❌"
        return f"M:{m}\nE:{e}"
    elif log_type == "Cook 🍳":
        return "✅" if row['morning_status'] == 'Present' else "❌"
    
    return "✅"

# Dialog for Entry
@st.dialog("Log Entry")
def entry_dialog(date_obj, log_type_ui, current_data=None):
    st.write(f"### {date_obj.strftime('%A, %d %B %Y')}")
    
    # Determine type key for backend
    type_map = {"Milk 🥛": "milk", "Maid 🧹": "maid", "Cook 🍳": "cook"}
    backend_type = type_map[log_type_ui]
    
    with st.form("entry_form"):
        payload = {'date': date_obj}
        
        if log_type_ui == "Milk 🥛":
            # Defaults
            def_del = True
            def_qty = 1.0
            if current_data is not None:
                def_del = bool(current_data['delivered'])
                def_qty = float(current_data['quantity'])
                
            is_delivered = st.checkbox("Delivered?", value=def_del)
            qty_input = st.number_input("Quantity (L)", value=def_qty, step=0.5, disabled=not is_delivered)
            payload.update({'delivered': is_delivered, 'quantity': qty_input if is_delivered else 0.0})
            
        elif log_type_ui == "Maid 🧹":
            def_m = True
            def_e = True
            if current_data is not None:
                def_m = (current_data['morning_status'] == 'Present')
                def_e = (current_data['evening_status'] == 'Present')
                
            c1, c2 = st.columns(2)
            with c1:
                m = st.checkbox("Morning", value=def_m)
            with c2:
                e = st.checkbox("Evening", value=def_e)
            payload.update({
                'morning_status': 'Present' if m else 'Absent',
                'evening_status': 'Present' if e else 'Absent'
            })
            
        elif log_type_ui == "Cook 🍳":
            def_m = True
            if current_data is not None:
                def_m = (current_data['morning_status'] == 'Present')
            
            m = st.checkbox("Morning Present", value=def_m)
            payload.update({'morning_status': 'Present' if m else 'Absent'})

        if st.form_submit_button("Save"):
            if save_entry(backend_type, payload):
                st.toast("Saved successfully!", icon="💾")
                st.rerun()

# Generic Calendar View
def render_calendar(log_type_ui):
    # Map UI name to backend key
    type_map = {"Milk 🥛": "milk", "Maid 🧹": "maid", "Cook 🍳": "cook"}
    backend_type = type_map[log_type_ui]
    
    # Controls for Month/Year
    today = datetime.date.today()
    
    col_l, col_m, col_r = st.columns([2, 1, 1])
    with col_l:
        st.subheader(f"{log_type_ui} Calendar")
    with col_m:
        sel_month = st.selectbox("Month", range(1, 13), index=today.month-1, format_func=lambda m: calendar.month_name[m])
    with col_r:
        sel_year = st.selectbox("Year", range(2023, 2031), index=today.year-2023)

    year = sel_year
    month = sel_month
    
    # Load data for the whole file then filter
    df = load_data(backend_type)
    
    # Stats row
    if not df.empty:
        # Filter for selected month
        temp_date = pd.to_datetime(df['date'])
        mask = (temp_date.dt.month == month) & (temp_date.dt.year == year)
        m_df = df[mask]
        
        c1, c2 = st.columns(2)
        if backend_type == 'milk':
            tot = m_df[m_df['delivered']==True]['quantity'].sum()
            c1.metric("Total Milk", f"{tot} L")
            absent = m_df[m_df['delivered']==False].shape[0]
            c2.metric("Days Absent", absent)
        elif backend_type == 'maid':
            abs_m = m_df[m_df['morning_status']=='Absent'].shape[0]
            abs_e = m_df[m_df['evening_status']=='Absent'].shape[0]
            c1.metric("Morning Absent", abs_m)
            c2.metric("Evening Absent", abs_e)
        elif backend_type == 'cook':
            abs_m = m_df[m_df['morning_status']=='Absent'].shape[0]
            c1.metric("Morning Absent", abs_m)
            
    st.divider()

    # Calendar Grid
    cal = calendar.Calendar(firstweekday=0) # 0 = Monday
    month_days = cal.monthdatescalendar(year, month)
    
    # Weekday Headers
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, d in enumerate(days):
        cols[i].markdown(f"**{d}**")
        
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month != month:
                cols[i].empty() # Skip other month days for cleanliness
                continue
                
            # Get existing data if any
            row_data = None
            if not df.empty:
                matches = df[df['date'] == day]
                if not matches.empty:
                    row_data = matches.iloc[0]
            
            icon = get_status_icon(log_type_ui, day, df)
            
            # Button Label
            label = f"{day.day}\n{icon}"
            
            # Highlight today (only if showing current month/year)
            if day == today:
                 label = f"TODAY\n{icon}"

            if cols[i].button(label, key=f"{backend_type}_{day}", use_container_width=True):
                entry_dialog(day, log_type_ui, row_data)

import pandas as pd # Ensure pandas is imported if not already handled by load_data import chain (safe to re-import)

render_calendar(page)

