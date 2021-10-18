# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import time
import datetime
from datetime import timedelta

import pandas as pd
import telebot
from telebot import types
import Calculation_control as cc
from bob_telegram_tools.utils import TelegramTqdm
from bob_telegram_tools.bot import TelegramBot
import matplotlib.pyplot as plt
import admin as a

bot = telebot.TeleBot("1877530579:AAEGD1dpLzU_gK9hhZmLeVhw_tIj2ctWUdA", parse_mode=None)
admin =  a.UserAndAdminControl(bot)

global_params_strat = cc.StrategyParams()
global_params_suit = cc.SuitcaseParams()
temp_msg = None

class GetSuitcaseParams:

    def fill(self, message, params):
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        msg = bot.send_message(message.chat.id, f'Введите сумму, на которую собирать портфель')
        bot.register_next_step_handler(msg, self.get_sum, params)

    def get_sum(self, message, params):
        # while self.amount == 0:
        try:
            params.amount = int(message.text)
            msg = bot.send_message(message.chat.id,
                                   f'Введите промежуток расчета параметра бета и альфа от 3,4,5,6,7,8,9,10,11,12 мес.')
            bot.register_next_step_handler(msg, self.get_time_to_comp_beta, params)
        except Exception:
            bot.send_message(message.chat.id, 'Ошибка. Цифрами, пожалуйста. Повторите ввод.')
            menu_history_backpack(message.chat.id)
            return

    def get_time_to_comp_beta(self, message, params):
        try:
            params.month_to_campulate_beta = int(message.text)

            if params.month_to_campulate_beta < 3 | params.month_to_campulate_beta > 12:
                bot.send_message(message.chat.id, 'Значение меньше 3 или больше 12')
                raise Exception

        except Exception:
            bot.send_message(message.chat.id, 'Ошибка. Цифрами, пожалуйста. Повторите ввод.')
            menu_history_backpack(message.chat.id)
            return

        bot.send_message(message.chat.id, f'Считаем портфель для ' + str(
            params.amount) + '$' + ' с длительностью расчетов бета в ' + str(
            params.month_to_campulate_beta) + ' мес.')

        calc = cc.CalculationControl()
        res = calc.calculate_suitcase(params)
        if len(res) > 4096:
            for x in range(0, len(res), 4096):
                bot.send_message(message.chat.id, res[x:x + 4096])
        else:
            bot.send_message(message.chat.id, res)
        global global_params_suit
        global_params_suit = params
        favorite_accept_suitcase(message)



class GetStrategyParams:
    def fill(self, message, params):
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        msg = bot.send_message(message.chat.id, f'ВВедите сумму, которую готовы потратить (в долларах)')
        bot.register_next_step_handler(msg, self.get_sum, params)

    def get_sum(self, message, params):
        # while self.amount == 0:
        try:
            params.amount = int(message.text)
        except Exception:
            bot.send_message(message.chat.id, 'Цифрами, пожалуйста. Повторите ввод.')
            menu_history_backpack(message.chat.id)
            return
        msg = bot.send_message(message.chat.id, f'ВВедите дату с которой начать просчет стратегии в формате дд.мм.гггг')
        bot.register_next_step_handler(msg, self.get_start_date, params)

    def get_start_date(self, message, params):
        # self.start_date == datetime.date(2011, 1, 1):
        try:
            params.start_date = datetime.datetime.strptime(message.text, '%d.%m.%Y')
            if params.start_date < datetime.datetime(2011, 1, 1):
                bot.send_message(message.chat.id, "Ошибка. Данные в базе начинаются с 2011-го года")
        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, "Введите дату в формате дд.мм.гггг. Цифрами. Повторите ввод.")
            menu_history_backpack(message.chat.id)

            return
        msg = bot.send_message(message.chat.id, f"Введите дату окончания периода просчета стратегии. Разница между "
                                                f"датами должна быть больше 3 месяцев")
        bot.register_next_step_handler(msg, self.get_end_time, params)

    def get_end_time(self, message, params):
        # while self.start_date == datetime.date(2011, 1, 1):
        try:
            params.end_date = datetime.datetime.strptime(message.text, '%d.%m.%Y')
            if (params.end_date - params.start_date).days < 90:
                raise Exception
            if params.end_date > datetime.datetime.today()- datetime.timedelta(days=1):
                bot.send_message(message.chat.id, "Ошибка. Стратегия может быть просчитана только до вчерашней даты. ")

        except Exception:
            bot.send_message(message.chat.id, "Введите дату в формате дд-мм-гггг. Цифрами. Разница между датами "
                                              "должна быть больше 3 месяцев. Повторите ввод.")
            menu_history_backpack(message.chat.id)
            return
        msg = bot.send_message(message.chat.id, f"Введите количество месяцев для удержания одного портфеля от 3 до 12.")
        bot.register_next_step_handler(msg, self.get_hold_time, params)

    def get_hold_time(self, message, params):
        # while params.hold_time == 0:
        try:
            params.hold_time = int(message.text)
            print(params.hold_time)
            if (params.hold_time < 3 | params.hold_time > 12):
                bot.send_message(message.chat.id, 'Значение меньше 3 или больше 12')
                raise Exception
            if ((params.end_date - params.start_date).days / 30 < params.hold_time):
                bot.send_message(message.chat.id, 'Вводимый промежуток больше чем период расчета стратегии.')
                raise Exception

        except Exception:
            bot.send_message(message.chat.id, 'Ошибка. Повторите ввод.')
            menu_history_backpack(message.chat.id)
            return
        msg = bot.send_message(message.chat.id,
                               'Введите промежуток расчета параметра бета и альфа от 4,5,6,7,8,9,10,11,12 мес.')
        bot.register_next_step_handler(msg, self.get_time_to_comp_beta, params)

    def get_time_to_comp_beta(self, message, params):
        try:
            params.month_to_campulate_beta = int(message.text)
            if (params.month_to_campulate_beta < 3 | params.month_to_campulate_beta > 12):
                bot.send_message(message.chat.id, 'Значение меньше 3 или больше 12')
                raise Exception

        except Exception:
            bot.send_message(message.chat.id, 'Цифрами, пожалуйста. Повторите ввод.')
            return

        bot.send_message(message.chat.id, f'Просчитываем стратегию для ' + str(params.amount) + '$, с периодами '
                                                                                                'удержания портфеля в- '
                                                                                                '' + str(
            params.hold_time)
                         + ' мес., с  ' + str(
            datetime.datetime.strftime(params.start_date, "%m.%d.%Y")) + ' по  ' + str(
            datetime.datetime.strftime(params.end_date, "%m.%d.%Y")) + ' с длительностью '
                                                                       'расчетов бета в ' + str(
            params.month_to_campulate_beta) + ' мес.')

        calc = cc.CalculationControl()
        pb_bot = TelegramBot("1877530579:AAEGD1dpLzU_gK9hhZmLeVhw_tIj2ctWUdA", message.chat.id)
        bot.send_message(message.chat.id, calc.calculate_strategy_history(params, pb_bot))
        img = open('C:\\Users\\gabid\\PycharmProjects\\pythonProject2\\graphs\\мой_график.png', 'rb') # ____________________________________туть
        bot.send_photo(message.chat.id, img)
        global global_params_strat
        global_params_strat = params
        print(global_params_strat)
        favorite_accept_strategy(message)

        #menu_start_work(message.chat.id)

        #add_in_history_strategy



@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.from_user.id,
                     f'Я инвестиционный бот. Приятно познакомиться, {message.from_user.first_name}. Моя задача состоит в сборе портфеля акций лично для вас.')
    menu_start_work(message.from_user.id)
    admin.start(message)

@bot.message_handler(commands=['stat'])
def stat_proc(message):
    ret = admin.stat(message)
    df1 = pd.DataFrame({'Период': ret[0][0],'Кол-во':ret[0][1] })
    df1.plot.bar(x='Период', y='Кол-во')
    plt.xticks(rotation=25, ha='right')
    plt.title('Кол-во зарегистрированных пользователей')
    plt.xlabel("Период")
    plt.ylabel("Кол-вл")
    plt.savefig('graphs/статистика1')
    img = open('C:\\Users\\gabid\\PycharmProjects\\pythonProject2\\graphs\\статистика1.png', 'rb') # ____________________________________туть
    bot.send_photo(message.chat.id, img)

    df1 = pd.DataFrame({'Период': ret[1][0], 'Кол-во': ret[1][1]})
    df1.plot.bar(x='Период', y='Кол-во')
    plt.xticks(rotation=25, ha='right')
    plt.title('Кол-во активных пользователей')
    plt.xlabel("Период")
    plt.ylabel("Кол-вл")
    plt.savefig('graphs/статистика2')
    img = open('C:\\Users\\gabid\\PycharmProjects\\pythonProject2\\graphs\\статистика2.png', 'rb')# ____________________________________туть
    bot.send_photo(message.chat.id, img)


@bot.message_handler(commands=['management'])
def manag_proc(message):
    admin.management(message)

@bot.message_handler(commands=['admin'], content_types=['text'])
def admin_proc(message):
    admin.admin(message)

@bot.message_handler(commands=['history'])
def history_proc(message):
    res = admin.history(message)

@bot.message_handler(commands=['favorite'])
def favorite_proc(message):
     admin.favorite(message)


def favorite_accept_strategy(message):
    keyboard_pack_info = types.InlineKeyboardMarkup()  # наша клавиатура
    key_info = types.InlineKeyboardButton(text='Да', callback_data='favorite_strategy_yes')
    keyboard_pack_info.add(key_info)  # добавляем кнопку в клавиатуру
    key_pack = types.InlineKeyboardButton(text='Нет', callback_data='favorite_strategy_no')
    keyboard_pack_info.add(key_pack)  # добавляем кнопку в клавиатуру
    bot.send_message(message.chat.id, text='Добавить в избранное?', reply_markup=keyboard_pack_info)

def favorite_accept_suitcase(message):
    keyboard_pack_info = types.InlineKeyboardMarkup()  # наша клавиатура
    key_info = types.InlineKeyboardButton(text='Да', callback_data='favorite_suitcase_yes')
    keyboard_pack_info.add(key_info)  # добавляем кнопку в клавиатуру
    key_pack = types.InlineKeyboardButton(text='Нет', callback_data='favorite_suitcase_no')
    keyboard_pack_info.add(key_pack)  # добавляем кнопку в клавиатуру
    bot.send_message(message.chat.id, text='Добавить в избранное?', reply_markup=keyboard_pack_info)


def menu_start_work(message):
    global temp_msg
    temp_msg = message
    keyboard_pack_info = types.InlineKeyboardMarkup()  # наша клавиатура
    key_info = types.InlineKeyboardButton(text='Справка', callback_data='info_help')
    keyboard_pack_info.add(key_info)  # добавляем кнопку в клавиатуру
    key_pack = types.InlineKeyboardButton(text='Сбор потрфеля', callback_data='pack_menu')
    keyboard_pack_info.add(key_pack)  # добавляем кнопку в клавиатуру
    '''
    key_info = types.InlineKeyboardButton(text="История", callback_data='history_request')
    keyboard_pack_info.add(key_info)
    key_info = types.InlineKeyboardButton(text="Избранное", callback_data='favorite_request')
    keyboard_pack_info.add(key_info)
    '''
    bot.send_message(message, text='Что вы хотите сделать? \n Для просмотра истории нажмите /history \n Для просмотра избранного нажмите /favorite', reply_markup=keyboard_pack_info)



def menu_info_help(message):
    keyboard_help_info = types.InlineKeyboardMarkup()  # наша клавиатура
    key_info = types.InlineKeyboardButton(text='Как работать с ботом ', callback_data='info')
    keyboard_help_info.add(key_info)  # добавляем кнопку в клавиатуру
    key_help = types.InlineKeyboardButton(text='Описание команд ', callback_data='help')
    keyboard_help_info.add(key_help)  # добавляем кнопку в клавиатуру
    bot.send_message(message, text='Что вы хотите узнать?', reply_markup=keyboard_help_info)


def menu_history_backpack(message):
    keyboard_history_backpack = types.InlineKeyboardMarkup()  # наша клавиатура
    key_history = types.InlineKeyboardButton(text='Посмотреть работу стратегии на исторических данных',
                                             callback_data='history_strategy')
    keyboard_history_backpack.add(key_history)  # добавляем кнопку в клавиатуру
    key_pack = types.InlineKeyboardButton(text='Собрать портфель', callback_data='collect_backpack')
    keyboard_history_backpack.add(key_pack)  # добавляем кнопку в клавиатуру
    bot.send_message(message, text='Что вы хотите сделать?', reply_markup=keyboard_history_backpack)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "info_help":
        menu_info_help(call.message.chat.id)
    elif call.data == "pack_menu":
        menu_history_backpack(call.message.chat.id)
    elif call.data == 'favorite_strategy_yes':
        bot.send_message(call.from_user.id, 'Запись занесена в избранное')
        admin.add_in_history_strategy(call.from_user.id, admin.get_user_name(call.from_user.id),
                                      global_params_strat.amount, global_params_strat.month_to_campulate_beta,
                                      global_params_strat.start_date, global_params_strat.end_date,
                                      global_params_strat.hold_time, 1)
        menu_start_work(call.message.chat.id)
    elif call.data == 'favorite_strategy_no':
        bot.send_message(call.from_user.id, 'Запись занесена в историю')
        admin.add_in_history_strategy(call.from_user.id, admin.get_user_name(call.from_user.id),
                                      global_params_strat.amount, global_params_strat.month_to_campulate_beta,
                                      global_params_strat.start_date, global_params_strat.end_date,
                                      global_params_strat.hold_time, 0)
        menu_start_work(call.message.chat.id)
    elif call.data == 'favorite_suitcase_yes':
        bot.send_message(call.from_user.id, 'Запись занесена в избранное')
        admin.add_in_history_suitcase(call.from_user.id, admin.get_user_name(call.from_user.id),
                                      global_params_suit.amount, global_params_suit.month_to_campulate_beta,
                                      1)
        menu_start_work(call.message.chat.id)
    elif call.data == 'favorite_suitcase_no':
        print(call.from_user.id)
        bot.send_message(call.from_user.id, 'Запись занесена в историю')
        admin.add_in_history_suitcase(call.from_user.id, admin.get_user_name(call.from_user.id),
                                      global_params_suit.amount, global_params_suit.month_to_campulate_beta,
                                      0)
        menu_start_work(call.message.chat.id)
    elif call.data == "info":
        show_info(call.message.chat.id)
        menu_start_work(call.message.chat.id)

    elif call.data == "history_request":
        msg = bot.send_message(call.message.chat.id, 'Сколько последних записей вы хотите видеть?')
        bot.register_next_step_handler(msg, admin.history_output)

    elif call.data == "favorite_request":
        msg = bot.send_message(call.message.chat.id, 'Сколько последних записей вы хотите видеть?')
        bot.register_next_step_handler(msg, admin.favorite_output)
    elif call.data == 'stat_users':
        admin.stat(call.message)
    elif call.data == "help":
        show_help(call.message.chat.id)
        menu_start_work(call.message.chat.id)
    elif call.data == "collect_backpack":
        process_back_pack(call.message)
    elif call.data == "history_strategy":
        process_strategy_history(call.message)
    elif call.data == 'add_admin':
        msg = bot.send_message(call.message.chat.id,
                               'Введите id пользователя, которого хотите повысить до администратора')
        bot.register_next_step_handler(msg, admin.add_admin)
    elif call.data == 'remove_admin':
        msg = bot.send_message(call.message.chat.id,
                               'Введите id администратора, которого хотите понизить до пользователя')
        bot.register_next_step_handler(msg, admin.remove_admin)
    elif call.data == 'watch_bd':
        data_base = admin.get_data_base()
        text = ""
        for user in data_base:
            text += "id: " + str(user[0]) + "\n"
            text += "id пользователя: " + str(user[1]) + "\n"
            text += "Имя и фамилия: " + str(user[2]) + "\n"
            text += "Роль пользователя: " + str(user[3]) + "\n"
            text += "Дата регистрации: " + str(user[4]) + "\n"
            text += "Последнее посещение: " + str(user[5]) + "\n"
            text += "\n"
        bot.send_message(call.message.chat.id, text)
    elif call.data == 'search_user':
        msg = bot.send_message(call.message.chat.id,
                               'Введите имя и фамилию пользователя, чтобы получить о нём информацию')
        bot.register_next_step_handler(msg, admin.search_user)
    elif call.data == 'change_pass':
        msg = bot.send_message(call.message.chat.id, "Введите новый пароль")
        bot.register_next_step_handler(msg, admin.change_pass)


@bot.message_handler(commands=['info'])
def show_info(message):
    bot.send_message(message,
                     "Наш бот был создан командой Студентов из Челгу в качестве практической работы. \nЕго целью является анализ рынка акции сбор потрфеля по определенной стратегии. \nБот может собрать порфтель на заданную сумму на текущий момент времени, либо вы можете на архивных данных посмотреть работу выбранной стратегии.")


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message,
                     'Команды: \n/info - Описание бота и его работы \n/help - Вывод команд \n/collect_backpack - Начать процесс сбора портфеля \n/strategy_history - Построить стратегию на исторических данных.\n/history - Показать историю запросов.\n/favorite - Показать Ваши избранные запросы.\n/stat - Показать статистику пользователей.\n/management - Вызов панели администратора.\n/admin - Зарегистрироваться как главный администратор.')


@bot.message_handler(commands=['collect_backpack'])
def process_back_pack(message):
    get_params = GetSuitcaseParams()
    params = cc.SuitcaseParams()
    get_params.fill(message, params)


@bot.message_handler(commands=['strategy_history'])
def process_strategy_history(message):
    get_params = GetStrategyParams()
    params = cc.StrategyParams()
    get_params.fill(message, params)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.from_user.id, 'Привет!')
    else:
        bot.send_message(message.from_user.id, 'Не понимаю, что это значит.')


bot.polling(none_stop=True)
