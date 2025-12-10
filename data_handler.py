import pandas as pd
import os
import datetime
import streamlit as st
from github import Github

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

def get_github_repo():
    """Returns the GitHub repo object if secrets are configured."""
    try:
        if "gt_token" in st.secrets and "github_repo" in st.secrets:
            g = Github(st.secrets["gt_token"])
            return g.get_repo(st.secrets["github_repo"])
    except Exception as e:
        print(f"GitHub Auth Error: {e}")
    return None

def fetch_from_github(config):
    """Attempts to fetch the CSV from GitHub and save it locally."""
    repo = get_github_repo()
    if not repo:
        return False
    
    file_path = config['file']
    try:
        contents = repo.get_contents(file_path)
        with open(file_path, "wb") as f:
            f.write(contents.decoded_content)
        return True
    except Exception as e:
        print(f"GitHub Fetch Error for {file_path}: {e}")
        return False

def sync_to_github(config, df):
    """Updates the file on GitHub with the current dataframe content."""
    repo = get_github_repo()
    if not repo:
        return False
        
    file_path = config['file']
    csv_content = df.to_csv(index=False)
    commit_msg = f"Automated Update: {file_path}"
    
    try:
        # Check if file exists to update, else create
        try:
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, commit_msg, csv_content, contents.sha)
        except:
             repo.create_file(file_path, commit_msg, csv_content)
        return True
    except Exception as e:
        print(f"GitHub Sync Error: {e}")
        return False

def load_data(log_type):
    """Loads the log data for a specific type. Tries GitHub if local missing."""
    config = LOG_CONFIG.get(log_type)
    if not config:
        return pd.DataFrame()

    file_path = config['file']
    
    # If local file doesn't exist, try fetching from GitHub first
    if not os.path.exists(file_path):
        fetch_from_github(config)

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
    """Saves a generic entry based on log type and syncs to GitHub."""
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
        # Save locally
        df.to_csv(config['file'], index=False)
        
        # Sync to GitHub
        sync_to_github(config, df)
        return True
    return False

def delete_entry(log_type, entry_date):
    """Deletes an entry for a specific date."""
    df = load_data(log_type)
    
    if isinstance(entry_date, datetime.datetime):
        entry_date = entry_date.date()
    
    # Remove entry for this date
    df = df[df['date'] != entry_date]
    
    config = LOG_CONFIG.get(log_type)
    if config:
        # Save locally
        df.to_csv(config['file'], index=False)
        
        # Sync to GitHub
        sync_to_github(config, df)
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

    # Logic: Range end is yesterday. If today is 1st, range is empty.
    end_date_limit = today - datetime.timedelta(days=1)
    
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
