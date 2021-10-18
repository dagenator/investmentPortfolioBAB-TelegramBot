import numpy as np
import sqlite3 as db
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
from datetime import date


class Parser:

    @staticmethod
    def create_diff_table(values):
        last_value = None
        result = []
        for value in values:
            if last_value is None:
                last_value = value
                continue
            result.append((dt.datetime.strptime(value[0], '%Y-%m-%d %H:%M:%S'), (value[1] / last_value[1]) - 1))
            last_value = value
        return result

    @staticmethod
    def create_join_table(name):
        with db.connect("notes.db") as con:
            cur = con.cursor()
            cur.execute("SELECT Date, Close FROM STOCK_HISTORY WHERE Name = ?", (name,))
            values = cur.fetchall()
        diff = Parser.create_diff_table(values)
        df = pd.DataFrame(diff, columns=['Date', 'DIFFERENCE'])
        df.to_sql(name='STOCK_DIFF', con=db.connect("notes.db"), if_exists='replace', index=False)
        cur.execute(
            "SELECT sd.Date, sd.DIFFERENCE, sp.DIFFERENCE FROM STOCK_DIFF sd JOIN SP500_DIFF sp on sd.Date = sp.Date")
        per = cur.fetchall()
        df = pd.DataFrame(per, columns=['Date', 'Company', 'SP'])
        cnx = db.connect("notes.db")
        df.to_sql(name='STOCK_SP_DIFF', con=cnx, if_exists='replace', index=False)

    @staticmethod
    def estimate_coef(x, y):
        n = np.size(x)
        m_x = np.mean(x)
        m_y = np.mean(y)
        SS_xy = np.sum(y * x) - n * m_y * m_x
        SS_xx = np.sum(x * x) - n * m_x * m_x
        b_1 = SS_xy / SS_xx
        b_0 = m_y - b_1 * m_x
        return b_0, b_1

    @staticmethod
    def get_value_from_tlist(tlist):
        points_x = []
        points_y = []
        for value in tlist:
            points_y.append(value[1])
            points_x.append(value[2])
        return points_x, points_y

    @staticmethod
    def create_stock_table(name, period):
        with db.connect("notes.db") as con:
            cur = con.cursor()
            cur.execute("SELECT MAX(DATE) FROM STOCK_TABLE_RE WHERE NAME = ? AND Period = ?", (name, period))
            last_date = cur.fetchone()[0]
            cur.execute("SELECT MAX(DATE) FROM STOCK_SP_DIFF")
            start_date = cur.fetchone()[0]
            if last_date is None:
                cur.execute("SELECT MIN(DATE) FROM STOCK_SP_DIFF WHERE DATE>?", (
                    (date.today() - relativedelta(years=10) + relativedelta(months=period)).strftime(
                        '%Y-%m-%d %H:%M:%S'),))
                last_date = cur.fetchone()[0]
            else:
                last_date = (dt.datetime.strptime(last_date, '%Y-%m-%d %H:%M:%S') + relativedelta(
                    months=period)).strftime('%Y-%m-%d %H:%M:%S')
            while start_date >= last_date:
                delta_date = (dt.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') - relativedelta(
                    months=period)).strftime(
                    '%Y-%m-%d %H:%M:%S')
                cur.execute("SELECT * FROM STOCK_SP_DIFF WHERE DATE < ? AND DATE > ?", (start_date, delta_date))
                values = cur.fetchall()
                values = Parser.get_value_from_tlist(values)
                x = np.array(values[0])
                y = np.array(values[1])
                b = Parser.estimate_coef(x, y)
                date_list = pd.date_range(start_date, periods=7).tolist()
                strokes = []
                close = Parser.get_cost_for_week(start_date)
                for i in date_list:
                    strokes.append((i, name, b[0], b[1], close, period))
                df = pd.DataFrame(strokes, columns=['DATE', 'NAME', 'ALPHA', 'BETA', 'COST', 'PERIOD'])
                df.to_sql(name='STOCK_TABLE_RE', con=db.connect('notes.db'), if_exists='append', index=False)
                start_date = (dt.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') - relativedelta(weeks=1)).strftime(
                    '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_cost_for_week(start_day):
        start_day = dt.datetime.strptime(start_day, '%Y-%m-%d %H:%M:%S')
        end_day = (start_day + relativedelta(weeks=1)).strftime('%Y-%m-%d')
        with db.connect("notes.db") as con:
            cur = con.cursor()
            cur.execute("SELECT Close FROM STOCK_HISTORY WHERE Date>=? AND Date<?",
                        (start_day.strftime('%Y-%m-%d'), end_day))
            values = cur.fetchall()
            sum_for_avg = 0.0
            for value in values:
                sum_for_avg += value[0]
            length = len(values)
            if length == 0:
                length = 1
            return sum_for_avg / length

    @staticmethod
    def create_stock_tables(name):
        for i in range(3, 13):
            Parser.create_stock_table(name, i)
