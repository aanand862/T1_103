import pandas as pd
import os
import datetime

# Schemas for different logs
LOG_CONFIG = {
    'milk': {
        'file': 'milk_log.csv',
        'columns': ['date', 'delivered', 'quantity']
    },
    'maid': {
        'file': 'maid_log.csv',
        'columns': ['date', 'morning_status', 'evening_status'] # status: "Present", "Absent"
    },
    'cook': {
        'file': 'cook_log.csv',
        'columns': ['date', 'morning_status'] # status: "Present", "Absent"
    }
}

def load_data(log_type):
    """Loads the log data for a specific type."""
    config = LOG_CONFIG.get(log_type)
    if not config:
        return pd.DataFrame()

    file_path = config['file']
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=config['columns'])
    
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    except Exception as e:
        print(f"Error loading {log_type} data: {e}")
        return pd.DataFrame(columns=config['columns'])

def save_entry(log_type, data_dict):
    """Saves a generic entry based on log type."""
    df = load_data(log_type)
    entry_date = data_dict['date']
    
    if isinstance(entry_date, datetime.datetime):
        entry_date = entry_date.date()
    
    # Remove existing entry for this date
    df = df[df['date'] != entry_date]
    
    new_entry = pd.DataFrame([data_dict])
    df = pd.concat([df, new_entry], ignore_index=True)
    df = df.sort_values(by='date')
    
    config = LOG_CONFIG.get(log_type)
    if config:
        df.to_csv(config['file'], index=False)
        return True
    return False

def get_missing_dates(log_type, year, month):
    """Returns a list of dates in the given month (up to yesterday) that have no entry."""
    df = load_data(log_type)
    
    today = datetime.date.today()
    
    # Decide the range: from 1st of month to MIN(yesterday, last day of month)
    # If month is future, return empty
    start_date = datetime.date(year, month, 1)
    if start_date > today:
        return []

    # End date (inclusive) for checking: yesterday? Or today?
    # Request said "missing log", usually implying past days.
    # Let's check up to yesterday to avoid annoying user about today if they just woke up.
    # Or check up to today if it's evening? Simpler: Check up to yesterday.
    
    # Logic: Range end is yesterday. If today is 1st, range is empty.
    end_date_limit = today - datetime.timedelta(days=1)
    
    # However, if we are looking at a past month, range is full month.
    # Logic: get all days in month, filter those <= end_date_limit
    
    # Generate all dates for the month
    # pd.date_range is useful
    # Handle end of month
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)
        
    last_day_of_month = next_month - datetime.timedelta(days=1)
    
    check_end_date = min(last_day_of_month, end_date_limit)
    
    if start_date > check_end_date:
        return []
        
    all_dates = pd.date_range(start_date, check_end_date).date
    
    existing_dates = pd.Series([])
    if not df.empty:
        existing_dates = df['date']
    
    missing = [d for d in all_dates if d not in existing_dates.values]
    return missing

def get_monthly_stats(log_type, year, month):
    """Generic stats retriever."""
    df = load_data(log_type)
    if df.empty:
        return df # Return empty generic DF for safe handling

    temp_df = df.copy()
    temp_df['date'] = pd.to_datetime(temp_df['date'])
    mask = (temp_df['date'].dt.year == year) & (temp_df['date'].dt.month == month)
    return temp_df[mask]
