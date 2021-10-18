import numpy as np
import sqlite3 as db
import investpy
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import date
import yfinance as yf
from Parser import Parser


class Downloader:
    @staticmethod
    def download_data(name):
        start = (date.today() - relativedelta(years=10)).strftime('%d/%m/%Y')
        end = (date.today() - relativedelta(days=1)).strftime('%d/%m/%Y')
        df = investpy.get_stock_historical_data(stock=name,
                                                country='United States',
                                                from_date=start,
                                                to_date=end)
        df['Name'] = name
        cnx = db.connect("notes.db")
        df.to_sql(name='STOCK_HISTORY', con=cnx, if_exists='replace')

    @staticmethod
    def update_sp500():
        start = (date.today() - relativedelta(years=10)).strftime('%Y-%m-%d')
        end = (date.today() - relativedelta(days=1)).strftime('%Y-%m-%d')
        df = yf.download('SPY', start=start, end=end)
        cnx = db.connect("notes.db")
        df.to_sql(name='SP500', con=cnx, if_exists='replace')
        with db.connect("notes.db") as con:
            cur = con.cursor()
            cur.execute("SELECT Date, Close FROM SP500")
            values = cur.fetchall()
        diff = Parser.create_diff_table(values)
        df = pd.DataFrame(diff, columns=['Date', 'DIFFERENCE'])
        df.to_sql(name='SP500_DIFF', con=cnx, if_exists='replace', index=False)

    @staticmethod
    def get_companies():
        result = []
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        df = table[0]
        per = df.Symbol
        for i in investpy.get_stocks_list(country='United States'):
            for j in per:
                if i == j:
                    result.append(i)
        return result
