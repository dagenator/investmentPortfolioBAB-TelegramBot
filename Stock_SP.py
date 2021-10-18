import sqlite3 as db
import pandas as pd
from dateutil.relativedelta import relativedelta
import datetime as dt
from Downloader import Downloader
from Parser import Parser


def get_last_date():
    with db.connect("notes.db") as con:
        cur = con.cursor()
        cur.execute("SELECT MAX(DATE) FROM STOCK_TABLE_RE")
        s_date = (dt.datetime.today() - relativedelta(days=1)).strftime('%Y-%m-%d')
        some_date = cur.fetchone()[0]
        if s_date < some_date:
            s_date = dt.datetime.strptime((dt.datetime.today() - relativedelta(days=1)).strftime('%Y-%m-%d'), '%Y-%m-%d')
        else:
            s_date = dt.datetime.strptime(some_date, '%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT MIN(DATE) FROM STOCK_TABLE_RE WHERE DATE>=? ",
                    (s_date.strftime('%Y-%m-%d %H:%M:%S'), ))
        return dt.datetime.strptime(cur.fetchone()[0], '%Y-%m-%d %H:%M:%S')


def select_ab(s_date, period):
    """Принимает дату datetime и период - число от 3 до 12"""
    with db.connect("notes.db") as con:
        cur = con.cursor()
        s_date = dt.datetime.strptime(s_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
        cur.execute("SELECT COST, NAME, BETA, ALPHA FROM STOCK_TABLE_RE WHERE DATE=? AND Period=?",
                    (s_date.strftime('%Y-%m-%d %H:%M:%S'), period))
        result = cur.fetchall()
        df = pd.DataFrame(result, columns=['cost', 'name', 'b', 'a'])
    return df


def update_tables():
    Downloader.update_sp500()
    for i in Downloader.get_companies():
        Downloader.download_data(i)
        Parser.create_join_table(i)
        Parser.create_stock_tables(i)
    with db.connect("notes.db") as con:
        cur = con.cursor()
        cur.execute("DELETE FROM STOCK_TABLE_RE WHERE ALPHA is NULL OR BETA is NULL or COST=0")
