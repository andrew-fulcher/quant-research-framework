import pandas as pd
import yfinance as yf
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

DATA_DIR.mkdir(exist_ok=True)

#takes in a string corresponding to a ticker. For example, "AAPL" for Apple
def update_data(ticker):
    #create file path. Change as needed for other users
    file_path = DATA_DIR / f"{ticker}.csv"

    #check if file path exists for this data. If not, download data set
    if not os.path.exists(file_path):
        data = yf.download(ticker, start="2020-01-01")
        data.columns = data.columns.get_level_values(0)

        #fetch current date
        ny_time = pd.Timestamp.now(tz="America/New_York")
        today = ny_time.date()

        #remove current day from data
        data = data[data.index.date < today]

        #create file for new data
        data.to_csv(file_path)

        return data

    #read data currently saved on computer
    #from csv file, dates need to be formatted
    data = pd.read_csv(file_path, index_col = "Date", parse_dates = ["Date"])

    #fetch date of most recent entry
    last_date = data.index.max()
    start_date = last_date.strftime("%Y-%m-%d")

    #download data from yfinance starting from last date, clean columns
    new_data = yf.download(ticker, start = start_date)
    new_data.columns = new_data.columns.get_level_values(0)

    #combine new and old data
    updated_data = pd.concat([data, new_data])

    #remove duplicates
    duplicate_mask = updated_data.index.duplicated(keep="last")
    updated_data = updated_data[~duplicate_mask]

    #fetch current date
    ny_time = pd.Timestamp.now(tz="America/New_York")
    today = ny_time.date()

    #remove current day from data
    updated_data = updated_data[updated_data.index.date < today]

    #overwrite old data file with updated data
    updated_data.to_csv(file_path)

    return updated_data