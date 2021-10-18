import telebot
from telebot import types
import sqlite3
import datetime as dt
import Calculation_control as cc

from bob_telegram_tools.utils import TelegramTqdm
from bob_telegram_tools.bot import TelegramBot

class UserAndAdminControl:
    def __init__(self, bot):
        self.bot = bot
    con = sqlite3.connect("users.db", check_same_thread=False)
    cursor = con.cursor()

    def add_user_in_db(self, user_id: int, user_name: str, user_role: str, registration_date: str, last_date: str):
        info = self.cursor.execute('SELECT * FROM USERS WHERE user_id=?', (user_id, ))
        if info.fetchone() is None:
            self.cursor.execute('INSERT INTO USERS (user_id, user_name, user_role, registration_date, last_date) VALUES (?, ?, ?, ?, ?)', (user_id, user_name, user_role, registration_date, last_date))
        self.con.commit()

    def add_in_history_suitcase(self, user_id: int, user_name: str, amount: int, month_to_campulate_beta: int, favorite: int):
        self.cursor.execute('INSERT INTO REQUESTS (user_id, user_name, amount, month_to_campulate_beta, favorite, strategy) VALUES (?, ?, ?, ?, ?, 0)', (user_id, user_name, amount, month_to_campulate_beta, favorite))
        self.con.commit()

    def add_in_history_strategy(self, user_id: int, user_name: str, amount: int, month_to_campulate_beta: int, start_date: str, end_date: str, hold_time: int, favorite: int):
        self.cursor.execute('INSERT INTO REQUESTS (user_id, user_name, amount, month_to_campulate_beta, start_date, end_date, hold_time, favorite, strategy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)', (user_id, user_name, amount, month_to_campulate_beta, start_date, end_date, hold_time, favorite))
        self.con.commit()

    def check_role(self, user_id: int):
        self.cursor.execute('SELECT user_role FROM USERS WHERE user_id=?', (user_id, ))
        info = self.cursor.fetchone()
        self.con.commit()
        return info[0]

    def check_exist(self, user_id: int):
        info = self.cursor.execute('SELECT * FROM USERS WHERE user_id=?', (user_id, ))
        return not(info.fetchone() is None)

    def check_exist_from_name(self, user_name: str):
        info = self.cursor.execute('SELECT * FROM USERS WHERE user_name=?', (user_name, ))
        return not(info.fetchone() is None)

    def check_history_exist(self, user_id: int):
        info = self.cursor.execute('SELECT * FROM REQUESTS WHERE user_id=?', (user_id, ))
        return not(info.fetchone() is None)

    def check_favorite_exist(self, user_id: int):
        info = self.cursor.execute("SELECT * FROM REQUESTS WHERE user_id=? AND favorite=1", (user_id, ))
        return not(info.fetchone() is None)

    def check_pass(self, password: str):
        info = self.cursor.execute('SELECT current_pass FROM PASS WHERE current_pass=?', (password, ))
        return not(info.fetchone() is None)

    def change_role(self, user_id: int, role: str):
        self.cursor.execute('UPDATE USERS SET user_role = ? WHERE user_id=?', (role, user_id, ))
        self.con.commit()

    def get_hadmin_role(self, user_id: int):
        self.cursor.execute("UPDATE USERS SET user_role = 'hadmin' WHERE user_id=?", (user_id, ))
        self.con.commit()

    def get_data_base(self):
        self.cursor.execute("SELECT * FROM USERS")
        table = self.cursor.fetchall()
        self.con.commit()
        return table

    def get_user_name(self, user_id: int):
        self.cursor.execute("SELECT user_name FROM USERS WHERE user_id = ?", (user_id, ))
        name = self.cursor.fetchone()
        return name[0]

    def get_history_requests(self, user_id: int, count: int):
        self.cursor.execute("SELECT amount, month_to_campulate_beta, start_date, end_date, hold_time, strategy FROM REQUESTS WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, count))
        return self.cursor.fetchall()

    def get_favorite_requests(self, user_id: int, count: int):
        self.cursor.execute("SELECT amount, month_to_campulate_beta, start_date, end_date, hold_time, strategy FROM REQUESTS WHERE user_id = ? AND favorite=1 ORDER BY id DESC LIMIT ?", (user_id, count))
        return self.cursor.fetchall()

    def search_user_from_name(self, name: str):
        self.cursor.execute('SELECT * FROM USERS WHERE user_name=?', (name, ))
        info = self.cursor.fetchall()
        self.con.commit()
        return info

    def update_last_date(self, user_id: int):
        self.cursor.execute("UPDATE USERS SET last_date = ? WHERE user_id=?", (str(dt.date.today()), user_id, ))
        self.con.commit()


    # @bot.message_handler(commands=['add_user'])
    def start(self, message):
        #self.bot.send_message(message.chat.id, "Привет, я тестовый чат-бот, чтобы узнать мои возможности введи команду /help")
        us_id = message.from_user.id
        us_name = message.from_user.first_name + ' ' + message.from_user.last_name
        us_date = str(dt.date.today())
        self.add_user_in_db(user_id=us_id, user_name=us_name, user_role='user', registration_date=us_date, last_date=us_date)

    # @bot.message_handler(commands=['history'])
    def history(self, message):
        self.update_last_date(message.from_user.id)
        if self.check_history_exist(message.from_user.id):
            msg = self.bot.send_message(message.chat.id, "Сколько последних записей Вы хотите видеть?")
            self.bot.register_next_step_handler(msg, self.history_output)
        else:
            self.bot.send_message(message.chat.id, "Ваша история пуста!")

    def history_output(self, message):
        self.update_last_date(message.from_user.id)
        msg = message.text
        if self.check_history_exist(message.from_user.id):
            if msg.isdigit():
                if 0 < int(msg) <= 1000000:
                    history = self.get_history_requests(message.from_user.id, int(msg))
                    text = ""
                    num = 1
                    for element in history:
                        if element[5] == 0:
                            text += str(num) + ") Считаем портфель для " + str(element[0]) + '$' + ", с длительностью расчётов бета в " + str(element[1]) + " мес.\n"
                        elif element[5] == 1:
                            text += str(num) + ") Просчитываем стратегию для " + str(element[0]) + '$' + ", с периодами удержания портефеля в " + str(element[4]) + " мес., с " + str(element[2]) + " по " + str(element[3]) + " с длительностью расчётов бета в " + str(element[1]) + " мес.\n"
                        num += 1
                    text += "Какой результат запроса Вы желаете повторить?"
                    msg = self.bot.send_message(message.chat.id, text)
                    self.bot.register_next_step_handler(msg, self.history_result)
                else:
                    self.bot.send_message(message.chat.id, "Число должно быть положительным и не больше 1000000")
            else:
                self.bot.send_message(message.chat.id, "Вы ввели некорректное число")
        else:
            self.bot.send_message(message.chat.id, "Ваша история пуста!")

    # @bot.message_handler(commands=['favorite'])
    def favorite(self, message):
        self.update_last_date(message.from_user.id)
        if self.check_favorite_exist(message.from_user.id):
            msg = self.bot.send_message(message.chat.id, "Сколько последних избранных записей Вы хотите видеть?")
            self.bot.register_next_step_handler(msg, self.favorite_output)
        else:
            self.bot.send_message(message.chat.id, "У Вас нет любимых записей :(")

    def favorite_output(self, message):
        self.update_last_date(message.from_user.id)
        msg = message.text
        if self.check_favorite_exist(message.from_user.id):
            if msg.isdigit():
                if 0 < int(msg) <= 1000000:
                    history = self.get_favorite_requests(message.from_user.id, int(msg))
                    text = ""
                    num = 1
                    for element in history:
                        if element[5] == 0:
                            text += str(num) + ") Считаем портфель для " + str(element[0]) + '$' + ", с длительностью расчётов бета в " + str(element[1]) + " мес.\n"
                        elif element[5] == 1:
                            text += str(num) + ") Просчитываем стратегию для " + str(element[0]) + '$' + ", с периодами удержания портефеля в " + str(element[4]) + " мес., с " + str(element[2]) + " по " + str(element[3]) + " с длительностью расчётов бета в " + str(element[1]) + " мес.\n"
                        num += 1
                    text += "Какой результат запроса Вы желаете повторить?"
                    msg = self.bot.send_message(message.chat.id, text)
                    self.bot.register_next_step_handler(msg, self.favorite_result)
                else:
                    self.bot.send_message(message.chat.id, "Число должно быть положительным и не больше 1000000")
            else:
                self.bot.send_message(message.chat.id, "Вы ввели некорректное число")
        else:
            self.bot.send_message(message.chat.id, "У Вас нет любимых записей :(")

    def history_result(self, message):
        msg = message.text
        calc =cc.CalculationControl()
        if msg.isdigit():
            if 0 < int(msg) <= 1000000:
                result = False
                data = None
                history = self.get_history_requests(message.from_user.id, int(msg))
                num = 1
                for element in history:
                    if num == int(msg):
                        result = True
                        data = element
                        break
                    num += 1
                if result == True and data[5] == 1:
                    params = cc.StrategyParams()
                    params.amount = data[0]
                    params.month_to_campulate_beta = data[1]
                    params.start_date = data[2]
                    params.end_date = data[3]
                    params.hold_time = data[4]
                    pb_bot = TelegramBot("1877530579:AAEGD1dpLzU_gK9hhZmLeVhw_tIj2ctWUdA", message.chat.id)
                    self.bot.send_message(message.chat.id, calc.calculate_strategy_history(params, pb_bot))
                    img = open('C:\\Users\\gabid\\PycharmProjects\\pythonProject2\\graphs\\мой_график.png', 'rb')
                    self.bot.send_photo(message.chat.id, img)
                elif result == True and data[5] == 0:
                    params = cc.SuitcaseParams()
                    params.amount = data[0]
                    params.month_to_campulate_beta = data[1]
                    res = calc.calculate_suitcase(params)
                    if len(res) > 4096:
                        for x in range(0, len(res), 4096):
                            self.bot.send_message(message.chat.id, res[x:x + 4096])
                    else:
                        self.bot.send_message(message.chat.id, res)
                else:
                    self.bot.send_message(message.chat.id, "Запрос не найден")
            else:
                self.bot.send_message(message.chat.id, "Число должно быть положительным и не больше 1000000")
        else:
            self.bot.send_message(message.chat.id, "Вы ввели неккоректное число")

    def favorite_result(self, message):
        msg = message.text
        calc = cc.CalculationControl()
        if msg.isdigit():
            if 0 < int(msg) <= 1000000:
                result = False
                data = None
                history = self.get_favorite_requests(message.from_user.id, int(msg))
                num = 1
                for element in history:
                    if num == int(msg):
                        result = True
                        data = element
                        break
                    num += 1
                if result == True and data[5] == 1:
                    params = cc.StrategyParams()
                    params.amount = data[0]
                    params.month_to_campulate_beta = data[1]
                    params.start_date = data[2]
                    params.end_date = data[3]
                    params.hold_time = data[4]
                    pb_bot = TelegramBot("1877530579:AAEGD1dpLzU_gK9hhZmLeVhw_tIj2ctWUdA", message.chat.id)
                    self.bot.send_message(message.chat.id, calc.calculate_strategy_history(params, pb_bot))
                    img = open('C:\\Users\\gabid\\PycharmProjects\\pythonProject2\\graphs\\мой_график.png', 'rb')
                    self.bot.send_photo(message.chat.id, img)
                elif result == True and data[5] == 0:
                    params = cc.SuitcaseParams()
                    params.amount = data[0]
                    params.month_to_campulate_beta = data[1]
                    res = calc.calculate_suitcase(params)
                    if len(res) > 4096:
                        for x in range(0, len(res), 4096):
                            self.bot.send_message(message.chat.id, res[x:x + 4096])
                    else:
                        self.bot.send_message(message.chat.id, res)
                else:
                    self.bot.send_message(message.chat.id, "Запрос не найден")
            else:
                self.bot.send_message(message.chat.id, "Число должно быть положительным и не больше 1000000")
        else:
            self.bot.send_message(message.chat.id, "Вы ввели неккоректное число")

    # @bot.message_handler(commands=['stat'])
    def stat(self, message):
        list_name1 =[]
        list_num1 =[]

        list_name2 = []
        list_num2 = []
        self.update_last_date(message.from_user.id)
        if not(self.check_role(message.from_user.id) == 'user'):
            text = "Количество зарегистрированных пользоваталей: \n"
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(registration_date) BETWEEN date('now', '-1 day') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За день: ' + str(tmp[0]) + '\n'
            list_name1.append('За день: ')
            list_num1.append(tmp[0])
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(registration_date) BETWEEN date('now', '-7 day') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За неделю: ' + str(tmp[0]) + '\n'
            list_name1.append('За неделю: ')
            list_num1.append(tmp[0])
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(registration_date) BETWEEN date('now', '-1 month') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За месяц: ' + str(tmp[0]) + '\n'
            list_name1.append('За месяц: ')
            list_num1.append(tmp[0])
            text += "\nКоличество активных пользователей: \n"
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(last_date) BETWEEN date('now', '-1 day') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За день: ' + str(tmp[0]) + '\n'
            list_name2.append('За день: ')
            list_num2.append(tmp[0])
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(last_date) BETWEEN date('now', '-7 day') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За неделю: ' + str(tmp[0]) + '\n'
            list_name2.append('За неделю: ')
            list_num2.append(tmp[0])
            self.cursor.execute("SELECT COUNT(*) FROM USERS WHERE date(last_date) BETWEEN date('now', '-1 month') AND date('now')")
            tmp = self.cursor.fetchone()
            text += 'За месяц: ' + str(tmp[0]) + '\n'
            list_name2.append('За месяц: ')
            list_num2.append(tmp[0])
            self.bot.send_message(message.chat.id, text)
            return ((list_name1, list_num1), (list_name2, list_num2 ))
        else:
            self.bot.send_message(message.chat.id, "У Вас нет доступа к общей статистике пользователей")

    # @bot.message_handler(commands=['management'])
    def management(self, message):
        self.update_last_date(message.from_user.id)
        user_role = self.check_role(message.from_user.id)
        if user_role == 'user':
            self.bot.send_message(message.chat.id, "У Вас нет доступа к управлению чат-ботом")
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            item = types.InlineKeyboardButton('Посмотреть базу данных пользователей', callback_data='watch_bd')
            item2 = types.InlineKeyboardButton('Добавить нового администратора', callback_data='add_admin')
            item3 = types.InlineKeyboardButton('Понизить администратора до пользователя', callback_data='remove_admin')
            item4 = types.InlineKeyboardButton('Информация о пользователе по имени', callback_data='search_user')
            item5 = types.InlineKeyboardButton('Смена пароля главного администратора', callback_data='change_pass')
            item6 = types.InlineKeyboardButton('Статистика пользователей', callback_data='stat_users')
            markup.add(item, item2, item3, item4, item5)
            self.bot.send_message(message.chat.id, 'Приветствую Вас, администратор!', reply_markup=markup)

    # @bot.message_handler(commands=['admin'], content_types=['text'])
    def admin(self, message):
        self.update_last_date(message.from_user.id)
        msg = self.bot.send_message(message.chat.id, 'Введите пароль, чтобы получить права администратора')
        self.bot.register_next_step_handler(msg, self.admin_check_pass)

    def admin_check_pass(self, message):
        if message.chat.type == 'private':
            if self.check_pass(message.text):
                self.get_hadmin_role(message.from_user.id)
                self.bot.send_message(message.chat.id, 'Теперь Вы администратор!')
            else:
                self.bot.send_message(message.chat.id, 'Неверный пароль!')

    # @bot.callback_query_handler(func=lambda call:True)

    def callback(self, call):
        if call.message:
            if call.data == 'add_admin':
                msg = self.bot.send_message(call.message.chat.id, 'Введите id пользователя, которого хотите повысить до администратора')
                self.bot.register_next_step_handler(msg, self.add_admin)
            elif call.data == 'remove_admin':
                msg = self.bot.send_message(call.message.chat.id, 'Введите id администратора, которого хотите понизить до пользователя')
                self.bot.register_next_step_handler(msg, self.remove_admin)
            elif call.data == 'watch_bd':
                data_base = self.get_data_base()
                text = ""
                for user in data_base:
                    text += "id: " + str(user[0]) + "\n"
                    text += "id пользователя: " + str(user[1]) + "\n"
                    text += "Имя и фамилия: " + str(user[2]) + "\n"
                    text += "Роль пользователя: " + str(user[3]) + "\n"
                    text += "Дата регистрации: " + str(user[4]) + "\n"
                    text += "Последнее посещение: " + str(user[5]) + "\n"
                    text += "\n"
                self.bot.send_message(call.message.chat.id, text)
            elif call.data == 'search_user':
                msg = self.bot.send_message(call.message.chat.id, 'Введите имя и фамилию пользователя, чтобы получить о нём информацию')
                self.bot.register_next_step_handler(msg, self.search_user)
            elif call.data == 'change_pass':
                msg = self.bot.send_message(call.message.chat.id, "Введите новый пароль")
                self.bot.register_next_step_handler(msg, self.change_pass)

    def add_admin(self, message):
        if message.chat.type == 'private':
            user_id = message.text
            if self.check_role(message.from_user.id) == 'hadmin':
                if self.check_exist(user_id):
                    if self.check_role(user_id) == 'user':
                        self.change_role(user_id, 'admin')
                        self.bot.send_message(message.chat.id, "Пользователь теперь администратор!")
                    else:
                        self.bot.send_message(message.chat.id, "Нельзя изменить роль этого пользователя")
                else:
                    self.bot.send_message(message.chat.id, "Пользователь не найден!")
            else:
                self.bot.send_message(message.chat.id, "У Вас нет прав, чтобы изменить роль пользователя")

    def remove_admin(self, message):
        if message.chat.type == 'private':
            user_id = message.text
            if self.check_role(message.from_user.id) == 'hadmin':
                if self.check_exist(user_id):
                    if self.check_role(user_id) == 'admin':
                        self.change_role(user_id, 'user')
                        self.bot.send_message(message.chat.id, "Администратор понижен до пользователя!")
                    else:
                        self.bot.send_message(message.chat.id, "Нельзя изменить роль этого пользователя")
                else:
                    self.bot.send_message(message.chat.id, "Пользователь не найден!")
            else:
                self.bot.send_message(message.chat.id, "У Вас нет прав, чтобы изменить роль пользователя")

    def search_user(self, message):
        if message.chat.type == 'private':
            name = message.text
            if not(self.check_role(message.from_user.id) == 'user'):
                if self.check_exist_from_name(name):
                    info = self.search_user_from_name(name)
                    text = ""
                    for user in info:
                        text += "id: " + str(user[0]) + "\n"
                        text += "id пользователя: " + str(user[1]) + "\n"
                        text += "Имя и фамилия: " + str(user[2]) + "\n"
                        text += "Роль пользователя: " + str(user[3]) + "\n"
                        text += "Дата регистрации: " + str(user[4]) + "\n"
                        text += "Последнее посещение: " + str(user[5]) + "\n"
                        text += "\n"
                    self.bot.send_message(message.chat.id, text)
                else:
                    self.bot.send_message(message.chat.id, "Такой пользователь не найден!")
            else:
                self.bot.send_message(message.chat.id, "У Вас нет прав для этой команды")

    def change_pass(self, message):
        if message.chat.type == 'private':
            if self.check_role(message.from_user.id) == 'hadmin':
                password = message.text
                self.cursor.execute("UPDATE PASS SET current_pass=?", (password, ))
                self.con.commit()
                self.bot.send_message(message.chat.id, "Пароль успешно изменён")
            else:
                self.bot.send_message(message.chat.id, "Ваших прав недостаточно, чтобы сменить пароль")