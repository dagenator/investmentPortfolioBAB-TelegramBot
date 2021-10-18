import datetime
from datetime import timedelta
import BABMath
import Stock_SP as bd
import pandas as pd
import matplotlib.pyplot as plt
import telebot
from telebot import types
from bob_telegram_tools.utils import TelegramTqdm
from bob_telegram_tools.bot import TelegramBot


class SuitcaseParams:
    amount = 0
    month_to_campulate_beta = 3


class StrategyParams:
    amount = 0
    start_date = datetime.date(2011, 1, 1)
    end_date = datetime.date(2011, 1, 1)
    hold_time = 0
    month_to_campulate_beta = 0  # int =1 0


class CalculationControl:

    def calculate_suitcase(self, params):
        last_date = bd.get_last_date()
        #last_date = datetime.datetime.strptime('07.07.2021', '%d.%m.%Y')

        df = bd.select_ab(last_date, params.month_to_campulate_beta)
        print(df)
        math = BABMath.Math()
        res = math.stock_procent_math(params.amount, df)
        text = ''
        text = 'Количество записей (акций):' + str(len(df)) + '\nДата последнего обновления базы данных: ' + str(
            last_date.date()) + '\n Cначала идут акции для сделки типа short, после long. Портфель:  \n '
        for i in range(2):
            for r in res[i][0]:
                text = text + '\n Акция: ' + str(r[1]) + 'В кол-ве: ' + str(r[0])
            text = text + '\n Итог по этому пакету акций составил :' + str(res[i][1])
        return text

    def calculate_strategy_history(self, params, pb_bot):

        math = BABMath.Math()
        current_day = params.start_date
        wallet = params.amount
        current_suitcase = 0
        date_cost = [(datetime.datetime.strftime(current_day, "%m.%d.%Y"), wallet)]
        short_cost = 0
        long_cost = 0
        dates = [current_day]
        timed = timedelta(days=params.hold_time * 30)
        while (params.end_date - current_day) > timed:
            current_day = current_day + datetime.timedelta(days=params.hold_time * 30)
            dates.append(current_day.date())
        dates.append(params.end_date.date())

        pb = TelegramTqdm(pb_bot)
        for d in pb(dates):
            df = bd.select_ab(d, params.month_to_campulate_beta)
            if (current_suitcase != 0):
                cost = 0
                cost = math.suitcase_cost(current_suitcase[1][0], df)
                wallet = wallet + cost
                wallet = wallet - short_cost
                date_cost.append((datetime.datetime.strftime(d, "%m.%d.%Y"), wallet))

            current_suitcase = math.stock_procent_math(wallet, df)
            short_cost = current_suitcase[0][1]
            long_cost = current_suitcase[1][1]
            wallet = wallet + short_cost - long_cost

        wallet = wallet + math.suitcase_cost(current_suitcase[1][0], df)
        wallet = wallet - short_cost

        return self.draw(date_cost, (wallet - params.amount) / params.amount)

    def draw(self, list, percent):
        last_date = bd.get_last_date()
        text = ''
        text = 'Дата последнего обновления базы данных: ' + str(datetime.datetime.strftime(last_date.date(),"%m.%d.%Y"))

        x_list = []
        y_list = []
        for i in list:
            x_list.append(i[0])
            y_list.append(i[1])
            text = text + '\n Дата: ' + str(i[0]) + ' Сумма: ' + str(i[1])

        text = text + '\n Итоговый процент прибыли = ' + str(percent)
        df = pd.DataFrame({'date': x_list, 'amount': y_list})

        df.plot(x='date', y='amount')

        # plt.figure(figsize=(200, 200))
        plt.xticks(rotation=25, ha='right')
        plt.xlabel("Дата")
        plt.ylabel("Сумма")
        plt.savefig('graphs/мой_график')
        return text
