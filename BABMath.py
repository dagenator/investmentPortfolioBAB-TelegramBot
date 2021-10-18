# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from itertools import combinations
import pandas as pd


class Math:
    def stock_procent_math(self, money, df):
        # Определяем значение Бэтта относительно которого идут расчеты
        border = 1

        # Делаем бета относительно фильтра
        under_border = df.loc[df["b"] <= border]
        weights_under = border - under_border['b']
        under_border = under_border.assign(
            fin_b=pd.Series(weights_under / (under_border['b'] * weights_under).sum()).values)

        above_border = df.loc[df["b"] > border]
        weights_above = above_border['b'] - border
        above_border = above_border.assign(
            fin_b=pd.Series(weights_above / (above_border['b'] * weights_above).sum()).values)

        under_border_beta_sum = under_border['fin_b'].sum()
        if under_border_beta_sum != 0:
            under_border['fin_b'] = under_border['fin_b'] / under_border_beta_sum
            above_border['fin_b'] = above_border['fin_b'] / under_border_beta_sum
        else:
            under_border['fin_b'] = under_border['fin_b'] * under_border_beta_sum
            above_border['fin_b'] = above_border['fin_b'] * under_border_beta_sum

        return self.money_dividing(money, above_border), self.money_dividing(money, under_border)

    def money_dividing(self, money, df1):
        df1 = df1.loc[df1["fin_b"] > 0]  # Отсавляем только то, у чего процент больше 0
        df1 = df1.sort_values(['fin_b'], ascending=False)

        total_percent = df1['fin_b'].sum()
        money = money * total_percent
        amount = 0
        free_percent = 0
        min_stock = ('', 0)
        stock_list = []
        for index, row in df1.iterrows():
            money_proc = row['cost'] / money
            if money_proc < row['fin_b'] + free_percent:
                __count = int((row['fin_b'] + free_percent) / money_proc)
                stock_list.append((int(__count), row['name']))
                free_percent = 0
                amount = amount + row['cost'] * __count
            else:
                free_percent = free_percent + row['fin_b']

        return (stock_list, amount)

    def suitcase_cost(self, list, df):
        amount = 0
        for l in list:
            name_seria = df.loc[df["name"] == l[1]]
            cost = name_seria['cost'].sum()
            amount = amount + (cost * l[0])
        return amount


if __name__ == '__main__':
    df = pd.DataFrame({
        'cost': [440, 220, 110, 780, 356, 547, 664],
        'name': ['A', 'B', 'C', 'D', 'F', 'H', 'E'],
        'b': [1.2, 1.1, 0.5, 0.8, 0.3, 2, 0.4],
        'a': [-0.1, 0.1, 0.5, -0.2, 0.2, -0.3, -0.1]
    })
    math = Math()

    print(math.stock_procent_math(2000, df))
    # do_suitcase(2000, df)
    # do_suit_case_beta_under_one(Money, Stock_cost, Stock_B_A)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
