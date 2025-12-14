
import unittest
import pandas as pd
import os
import shutil
from unittest.mock import patch
from data_handler import save_milk_finance, get_milk_finance, LOG_CONFIG

# Mocking the file path to avoid messing with real data during test
TEST_FILE = 'test_milk_finance.csv'

class TestMilkFinance(unittest.TestCase):
    
    def setUp(self):
        # Point the config to a test file
        self.original_file = LOG_CONFIG['milk_finance']['file']
        LOG_CONFIG['milk_finance']['file'] = TEST_FILE
        # Ensure clean state
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)
            
    def tearDown(self):
        # Restore config and clean up
        LOG_CONFIG['milk_finance']['file'] = self.original_file
        if os.path.exists(TEST_FILE):
            os.remove(TEST_FILE)

    @patch('data_handler.fetch_from_github', return_value=False)
    @patch('data_handler.sync_to_github', return_value=True)
    def test_save_and_retrieve_current_month(self, mock_sync, mock_fetch):
        """Test saving data for a specific month and retrieving it."""
        year, month = 2024, 5
        rate = 60.0
        advance = 1000.0
        
        save_milk_finance(year, month, rate, advance)
        
        # Verify file exists
        self.assertTrue(os.path.exists(TEST_FILE))
        
        # Verify retrieval
        data = get_milk_finance(year, month)
        self.assertEqual(data['rate'], 60.0)
        self.assertEqual(data['advance'], 1000.0)

    @patch('data_handler.fetch_from_github', return_value=False)
    @patch('data_handler.sync_to_github', return_value=True)
    def test_update_existing_month(self, mock_sync, mock_fetch):
        """Test updating data for an existing month."""
        year, month = 2024, 5
        save_milk_finance(year, month, 60.0, 1000.0)
        
        # Update
        save_milk_finance(year, month, 65.0, 1500.0)
        
        data = get_milk_finance(year, month)
        self.assertEqual(data['rate'], 65.0)
        self.assertEqual(data['advance'], 1500.0)
        
        # Ensure only one row for this month in csv
        df = pd.read_csv(TEST_FILE)
        self.assertEqual(len(df), 1)

    @patch('data_handler.fetch_from_github', return_value=False)
    @patch('data_handler.sync_to_github', return_value=True)
    def test_rate_propagation(self, mock_sync, mock_fetch):
        """Test that rate is picked up from previous month if missing for current."""
        # Save for April
        save_milk_finance(2024, 4, 55.0, 500.0)
        
        # Get for May (should get rate 55.0, advance 0.0)
        data = get_milk_finance(2024, 5)
        self.assertEqual(data['rate'], 55.0)
        self.assertEqual(data['advance'], 0.0)
        
        # Get for June
        data = get_milk_finance(2024, 6)
        self.assertEqual(data['rate'], 55.0) # Should still be 55 from April
        
        # Add entry for May distinct from April
        save_milk_finance(2024, 5, 60.0, 0.0)
        
        # Now June should see May's rate
        data = get_milk_finance(2024, 6)
        self.assertEqual(data['rate'], 60.0)

    @patch('data_handler.fetch_from_github', return_value=False)
    @patch('data_handler.sync_to_github', return_value=True)
    def test_future_month_isolation(self, mock_sync, mock_fetch):
        """Test that a future month's rate doesn't affect current month if current doesn't exist."""
        # Save for June
        save_milk_finance(2024, 6, 70.0, 0.0)
        
        # Get for May (should not see June's rate)
        data = get_milk_finance(2024, 5)
        self.assertEqual(data['rate'], 0.0)

    @patch('data_handler.fetch_from_github', return_value=False)
    @patch('data_handler.sync_to_github', return_value=True)
    def test_different_years(self, mock_sync, mock_fetch):
        """Test rate propagation across years."""
        # Dec 2023
        save_milk_finance(2023, 12, 50.0, 0.0)
        
        # Jan 2024
        data = get_milk_finance(2024, 1)
        self.assertEqual(data['rate'], 50.0)

if __name__ == '__main__':
    unittest.main()
