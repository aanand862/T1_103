import streamlit as st
import datetime
import calendar
from data_handler import save_entry, load_data, delete_entry

# Page config
st.set_page_config(
    page_title="T1-103 Utilities APP",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="auto"
)

# Custom CSS for mobile-responsive design
st.markdown("""
<style>
    /* Base responsive font sizing */
    html {
        font-size: clamp(14px, 2vw, 16px);
    }
    
    /* Mobile-optimized buttons with touch-friendly sizing */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 60px;
        min-height: 44px; /* Minimum touch target size */
        font-weight: bold;
        border: 1px solid #ddd;
        font-size: clamp(0.75rem, 2vw, 0.9rem);
        padding: 8px 4px;
        line-height: 1.2;
        transition: all 0.2s ease;
    }
    
    .stButton>button:active {
        transform: scale(0.98);
        background-color: #f0f0f0;
    }
    
    /* Highlight today's date with light orange background */
    .stButton button[kind="primary"] {
        background-color: #FFE5CC !important; /* Light orange background */
        border: 2px solid #FF8C00 !important;
        color: #000 !important;
    }
    
    /* Responsive metrics */
    [data-testid="stMetricValue"] {
        font-size: clamp(1.2rem, 3vw, 1.5rem);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: clamp(0.8rem, 2vw, 1rem);
    }
    
    /* Mobile-specific optimizations */
    @media (max-width: 768px) {
        /* Reduce button height on mobile for better fit */
        .stButton>button {
            height: 50px;
            font-size: 0.75rem;
            padding: 6px 2px;
        }
        
        /* Optimize title sizing */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        /* Better spacing for mobile */
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Optimize form inputs for touch */
        input[type="number"], 
        input[type="text"],
        input[type="date"] {
            font-size: 16px !important; /* Prevents zoom on iOS */
            min-height: 44px;
        }
        
        /* Better checkbox sizing */
        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }
        
        /* Optimize selectbox for mobile */
        [data-baseweb="select"] {
            font-size: 0.9rem;
        }
        
        /* Stack columns better on mobile */
        [data-testid="column"] {
            padding: 0.25rem !important;
        }
        
        /* Improve dialog sizing on mobile */
        [data-testid="stDialog"] {
            width: 95vw !important;
            max-width: 95vw !important;
        }
        
        /* Better metric display on mobile */
        [data-testid="stMetric"] {
            padding: 0.5rem;
        }
    }
    
    /* Extra small screens */
    @media (max-width: 480px) {
        .stButton>button {
            height: 45px;
            font-size: 0.7rem;
            padding: 4px 2px;
        }
        
        h1 {
            font-size: 1.3rem !important;
        }
        
        /* Tighter spacing for very small screens */
        .block-container {
            padding-left: 0.25rem !important;
            padding-right: 0.25rem !important;
        }
    }
    
    /* Improve radio button navigation */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }
    
    /* Better form submit button */
    .stButton button[kind="primary"],
    .stButton button[type="submit"] {
        background-color: #4CAF50;
        color: white;
        font-size: 1rem;
        height: 48px;
        min-height: 48px;
    }
</style>
""", unsafe_allow_html=True)

st.title("T1-103 Utilities APP 🏠")

# Sidebar navigation
page = st.sidebar.radio("Navigate", ["Milk 🥛", "Maid 🧹", "Cook 🍳"])

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
    
    
    if log_type_ui == "Milk 🥛":
        # Defaults
        def_del = True
        def_qty = 1.0
        if current_data is not None:
            def_del = bool(current_data['delivered'])
            def_qty = float(current_data['quantity'])
        
        # Checkbox OUTSIDE form for reactive behavior
        is_delivered = st.checkbox("Delivered?", value=def_del, key=f"delivered_{date_obj}")
        
        with st.form("entry_form"):
            payload = {'date': date_obj}
            
            # Only show quantity input if delivered
            if is_delivered:
                qty_input = st.number_input("Quantity (L)", value=def_qty, step=0.5)
                payload.update({'delivered': True, 'quantity': qty_input})
            else:
                payload.update({'delivered': False, 'quantity': 0.0})

            if st.form_submit_button("Save", type="primary"):
                if save_entry(backend_type, payload):
                    st.toast("Saved successfully!", icon="💾")
                    st.rerun()
        
        # Reset button outside form - only for today and future dates
        today = datetime.date.today()
        if date_obj >= today and current_data is not None:
            if st.button("🗑️ Reset Entry", key=f"reset_{date_obj}", use_container_width=True):
                if delete_entry(backend_type, date_obj):
                    st.toast("Entry deleted!", icon="🗑️")
                    st.rerun()
        
    elif log_type_ui == "Maid 🧹":
        def_m = True
        def_e = True
        if current_data is not None:
            def_m = (current_data['morning_status'] == 'Present')
            def_e = (current_data['evening_status'] == 'Present')
        
        with st.form("entry_form"):
            payload = {'date': date_obj}
            c1, c2 = st.columns(2)
            with c1:
                m = st.checkbox("Morning", value=def_m)
            with c2:
                e = st.checkbox("Evening", value=def_e)
            payload.update({
                'morning_status': 'Present' if m else 'Absent',
                'evening_status': 'Present' if e else 'Absent'
            })

            if st.form_submit_button("Save", type="primary"):
                if save_entry(backend_type, payload):
                    st.toast("Saved successfully!", icon="💾")
                    st.rerun()
        
        # Reset button outside form - only for today and future dates
        today = datetime.date.today()
        if date_obj >= today and current_data is not None:
            if st.button("🗑️ Reset Entry", key=f"reset_{date_obj}", use_container_width=True):
                if delete_entry(backend_type, date_obj):
                    st.toast("Entry deleted!", icon="🗑️")
                    st.rerun()
        
    elif log_type_ui == "Cook 🍳":
        def_m = True
        if current_data is not None:
            def_m = (current_data['morning_status'] == 'Present')
        
        with st.form("entry_form"):
            payload = {'date': date_obj}
            m = st.checkbox("Morning Present", value=def_m)
            payload.update({'morning_status': 'Present' if m else 'Absent'})

            if st.form_submit_button("Save", type="primary"):
                if save_entry(backend_type, payload):
                    st.toast("Saved successfully!", icon="💾")
                    st.rerun()
        
        # Reset button outside form - only for today and future dates
        today = datetime.date.today()
        if date_obj >= today and current_data is not None:
            if st.button("🗑️ Reset Entry", key=f"reset_{date_obj}", use_container_width=True):
                if delete_entry(backend_type, date_obj):
                    st.toast("Entry deleted!", icon="🗑️")
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
    
    # Weekday Headers - using HTML for better mobile control
    weekday_html = """
    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-bottom: 8px; text-align: center; font-weight: bold; font-size: 0.9rem;">
        <div>Mon</div>
        <div>Tue</div>
        <div>Wed</div>
        <div>Thu</div>
        <div>Fri</div>
        <div>Sat</div>
        <div>Sun</div>
    </div>
    """
    st.markdown(weekday_html, unsafe_allow_html=True)
        
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
            is_today = (day == today)
            if is_today:
                 label = f"TODAY\n{icon}"
            
            # Use primary button type for today to apply custom styling
            if cols[i].button(label, key=f"{backend_type}_{day}", use_container_width=True, type="primary" if is_today else "secondary"):
                entry_dialog(day, log_type_ui, row_data)

import pandas as pd # Ensure pandas is imported if not already handled by load_data import chain (safe to re-import)

render_calendar(page)

