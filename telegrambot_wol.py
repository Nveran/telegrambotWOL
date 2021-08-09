from models import Computer
from models import User
import configparser
import telebot
from telebot import types
from wakeonlan import send_magic_packet
from time import sleep

# работа с файлом token
config = configparser.ConfigParser()  # создаём объекта парсера
config.read("token.ini")  # читаем токен

# подключение токена
bot = telebot.TeleBot(config['Token']['token'])

# названия кнопок
YES_MSG = 'да'
NO_MSG = 'нет'
TURN_ON_PC = 'ВКЛЮЧИТЬ ПК'
ADD_NEW_COMPUTER = 'ДОБАВИТЬ НОВЫЙ ПК'
DELETE_COMPUTER = 'УДАЛИТЬ ПК'
MENU = 'ГЛАВНОЕ МЕНЮ'
REPEAT = 'НАЧАТЬ ЗАНОВО'


# создает нужные таблицы при первом запуске в бд
User.create_table()
Computer.create_table()


# проверяет наличие записей
def checking_records():
    is_exists = User.select().exists()
    return is_exists


# сверяет пользователя с базой
def check_user_in_users(user_telegram_id):
    user = User.select().where(User.telegram_id == user_telegram_id).first()
    if user is None:
        return False
    elif user_telegram_id == user.telegram_id:
        return True


# для создания объектов введенных данных
class TempRegistrationField:
    def __init__(self, telegram_id, field_name, value):
        self.telegram_id = telegram_id
        self.field_name = field_name
        self.value = value


# подставляет конкретные имена компов для конкретного пользователя
def buttons_comp(user_telegram_id):
    buttons = set()
    for computer in Computer.select().join(User).where(User.telegram_id == user_telegram_id):
        buttons.add(computer.computer_name)
    return buttons


# поведение при команде /start
@bot.message_handler(content_types=['text'])
def start_message(message):
    # проверка первого запуска и отправка меню
    if checking_records() and check_user_in_users(message.chat.id) and message.text in ('/start', MENU, NO_MSG):
        keyboard = telebot.types.ReplyKeyboardMarkup()
        keyboard.row(MENU)
        keyboard.row(TURN_ON_PC)
        keyboard.row(ADD_NEW_COMPUTER)
        keyboard.row(DELETE_COMPUTER)
        bot.send_message(
            message.chat.id,
            'Выберите, что вы хотите сделать?',
            reply_markup=keyboard
        )
    # показывает список сохраненных пк на включение
    elif check_user_in_users(message.chat.id) and message.text == TURN_ON_PC:
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(MENU)
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            'Выберите, какой пк вы хотите включить:',
            reply_markup=keyboard
        )
    # включает выбранный компьютер
    elif check_user_in_users(message.chat.id) and message.text in (buttons_comp(message.chat.id)):
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(MENU)
        keyboard.add(*buttons)
        computer = Computer.select().join(User).where(Computer.computer_name == message.text,
                                                      User.telegram_id == message.chat.id).first()
        send_magic_packet(computer.mac_address, ip_address=computer.ip_address, port=computer.port)
        bot.send_message(
            message.chat.id,
            f'Включен пк: "{computer.computer_name}" \n'
            'Вы можете включить еще один пк, или выйти в меню.',
            reply_markup=keyboard
        )
    # начинает процесс первой регистрации
    elif checking_records() is False and message.text in ('/start', REPEAT):
        keyboard = telebot.types.ReplyKeyboardMarkup()
        keyboard.row(YES_MSG, NO_MSG)
        bot.send_message(
            message.chat.id,
            'Приветствую, это первый запуск telegrambot_wol.\nДавайте проведем'
            f' первоначальную настройку. \nВаш id: {message.chat.id}\n'
            'Хотите его сохранить, как id администратора, и начать настройку?',
            reply_markup=keyboard
        )
        registration_values = set()
        registration_values.add(TempRegistrationField(message.chat.id, 'telegram_id', message.chat.id))
        bot.register_next_step_handler(message, registration, registration_values)
    # начинает процесс регистрации нового пк
    elif check_user_in_users(message.chat.id) and message.text == ADD_NEW_COMPUTER:
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(YES_MSG, NO_MSG)
        bot.send_message(
            message.chat.id,
            'Хотите добавить новый компьютер?',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, add_new_computer)
    # начинает процесс удаления пк из базы
    elif check_user_in_users(message.chat.id) and message.text == DELETE_COMPUTER:
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(YES_MSG, NO_MSG)
        bot.send_message(
            message.chat.id,
            'Хотите удалить пк?',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, choice_computer)


def add_new_computer(message):
    if message.text == YES_MSG:
        registration_values = set()
        bot.send_message(
            message.chat.id,
            'Укажите MAC address Вашего компьютера',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(message, retrieve_mac_address, registration_values)
    elif message.text == NO_MSG:
        start_message(message)


def choice_computer(message):
    if message.text == YES_MSG:
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(MENU)
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            'Какой пк вы хотите удалить?:',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, delete_computer)
    elif message.text == NO_MSG:
        start_message(message)


def delete_computer(message):
    if message.text in (buttons_comp(message.chat.id)):
        keyboard = telebot.types.ReplyKeyboardMarkup()
        keyboard.row(MENU)
        keyboard.row(ADD_NEW_COMPUTER)
        keyboard.row(TURN_ON_PC)
        computer = Computer.select().join(User).where(Computer.computer_name == message.text,
                                                      User.telegram_id == message.chat.id).first()
        computer.delete_instance()
        bot.send_message(
            message.chat.id,
            f'Компьютер: "{computer.computer_name}" удален.',
            reply_markup=keyboard
        )
    elif message.text == MENU:
        start_message(message)


def registration(message, registration_values):
    if message.text == YES_MSG:
        bot.send_message(
            message.chat.id,
            'Хорошо, тогда начнем.\nКак вы хотите, чтобы я к вам обращался?',
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(message, retrieve_user_name, registration_values)
    elif message.text == NO_MSG:
        bot.send_message(
            message.chat.id,
            'Бот не будет работать, пока не пройден этап регистрации, '
            'если вы не '
            'хотите, чтобы этот аккаунт был использован как аккаунт '
            'администратора, '
            'зайдите с нужного аккаунта и обратитесь к боту командой /start',
            reply_markup=types.ReplyKeyboardRemove()
        )


def retrieve_user_name(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'user_name', message.text))
    bot.send_message(
        message.chat.id,
        'Принято!\nТеперь нужно указать MAC address Вашего компьютера'
    )
    bot.register_next_step_handler(message, retrieve_mac_address, registration_values)


def retrieve_mac_address(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'mac_address', message.text))
    bot.send_message(
        message.chat.id,
        'Теперь, укажите ip address вашего ПК в локальной сети, или Broadcast '
        'вашей локальной сети. Например, если адрес вашего роутера 192.168.1.1'
        ' то Broadcast будет 192.168.1.255. Если не хотите заморачиваться,'
        ' можно просто указать ip address вашего ПК :). Узнать его можно,'
        ' введя в командную строку вашего ПК команду:\nipconfig'
    )
    bot.register_next_step_handler(message, retrieve_ip_address, registration_values)


def retrieve_ip_address(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'ip_address', message.text))
    bot.send_message(
        message.chat.id,
        'Теперь, укажите порт вашего пк. '
        'Это порт на который приходит "магический пакет" он же "Wake on LAN", '
        'в большинстве случаев равен 9 или 7. (Обычно 9).'
    )
    bot.register_next_step_handler(message, retrieve_port, registration_values)


def retrieve_port(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'port', message.text))
    bot.send_message(
        message.chat.id,
        'Ну а теперь, укажите, как будет называться ваш ПК в кнопках бота :)'
    )
    bot.register_next_step_handler(message, retrieve_computer_name, registration_values)


def retrieve_computer_name(message, registration_values):
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row(YES_MSG, NO_MSG)
    registration_values.add(TempRegistrationField(message.chat.id, 'computer_name', message.text))
    telegram_id = None
    user_name = None
    computer_name = None
    mac_address = None
    ip_address = None
    port = None
    for field in registration_values:
        if field.telegram_id != message.chat.id:
            continue
        if field.field_name == 'telegram_id':
            telegram_id = field.value
        elif field.field_name == 'user_name':
            user_name = field.value
        elif field.field_name == 'computer_name':
            computer_name = field.value
        elif field.field_name == 'mac_address':
            mac_address = field.value
        elif field.field_name == 'ip_address':
            ip_address = field.value
        elif field.field_name == 'port':
            port = field.value
    # для добавления пк
    if telegram_id is None and user_name is None and check_user_in_users(message.chat.id):
        telegram_id = message.chat.id
        username = User.select().where(User.telegram_id == message.chat.id).first()
        user_name = username.user_name
        bot.send_message(
            message.chat.id,
            'Настройка завершена!\n'
            f'Ваш id telegram: {telegram_id}\n'
            f'Ваше имя: {user_name}\n'
            f'Имя вашего ПК: {computer_name}\n'
            f'MAC address: {mac_address}\n'
            f'IP address: {ip_address}\n'
            f'Port: {port}\n'
            'Все верно? ',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, save_registration, telegram_id, user_name, computer_name, mac_address,
                                       ip_address, port)
    # для первой регистрации
    else:
        bot.send_message(
            message.chat.id,
            'Настройка завершена!\n'
            f'Ваш id telegram: {telegram_id}\n'
            f'Ваше имя: {user_name}\n'
            f'Имя вашего ПК: {computer_name}\n'
            f'MAC address: {mac_address}\n'
            f'IP address: {ip_address}\n'
            f'Port: {port}\n'
            'Все верно? ',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, save_registration, telegram_id, user_name, computer_name, mac_address,
                                       ip_address, port)


def save_registration(message, telegram_id, user_name, computer_name, mac_address, ip_address, port):
    # для первой регистрации
    if message.text == YES_MSG and telegram_id == message.chat.id and checking_records() is False:
        users_str = User(telegram_id=telegram_id, user_name=user_name, admin=1)
        computer_str = Computer(user_id=users_str, computer_name=computer_name, mac_address=mac_address,
                                ip_address=ip_address, port=port)
        users_str.save()
        computer_str.save()
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(MENU)
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            'Изменения сохранены! Можете выбрать, какой компьютер включить.',
            reply_markup=keyboard
        )
    elif message.text == NO_MSG and telegram_id == message.chat.id and checking_records() is False:
        keyboard = telebot.types.ReplyKeyboardMarkup()
        keyboard.row(REPEAT)
        bot.send_message(
            message.chat.id,
            'Хорошо, тогда попробуем начать регистрацию заново.',
            reply_markup=keyboard)
    # для добавления пк
    elif message.text == YES_MSG and telegram_id == message.chat.id and check_user_in_users(message.chat.id):
        user = User.select().where(User.telegram_id == message.chat.id).first()
        computer_str = Computer(user_id=user.id, computer_name=computer_name, mac_address=mac_address,
                                ip_address=ip_address, port=port)
        computer_str.save()
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(MENU)
        keyboard.add(*buttons)
        bot.send_message(
            message.chat.id,
            'Изменения сохранены! Можете выбрать, какой компьютер включить.',
            reply_markup=keyboard)
    elif message.text == NO_MSG and telegram_id == message.chat.id and check_user_in_users(message.chat.id):
        bot.send_message(
            message.chat.id,
            'Вы отказались сохранить, и вышли в главное меню. Если хотите '
            'попробовать еще раз, выберете нужную кнопку')
        start_message(message)

# метод связи с API Telegram
# цикл, чтобы бот не падал при отключении интернета
while True:
    try:
        bot.polling(none_stop=True)
    except Exception:
        sleep(1)
