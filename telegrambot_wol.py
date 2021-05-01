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

# переменные для кнопок клавиатуры и реакции на них
NO_MSG = 'нет'
YES_MSG = 'да'
ON_COMPUTER_MSG = 'включи компьютер'
WORK_CHEK_MSG = 'проверка работы бота'


User.create_table()
Computer.create_table()


def checking_records():
    is_exists = User.select().exists()
    return is_exists


def check_user_in_users(user_telegram_id):
    user = User.select().where(User.telegram_id == user_telegram_id).first()
    if user is None:
        return False
    elif user_telegram_id == user.telegram_id:
        return True


# включение кнопок клавиатуры в боте
keyboard1 = telebot.types.ReplyKeyboardMarkup()
keyboard2 = telebot.types.ReplyKeyboardMarkup()
keyboard1.row(YES_MSG, NO_MSG)
keyboard2.row(ON_COMPUTER_MSG, WORK_CHEK_MSG)


# для создания объектов введенных данных
class TempRegistrationField:
    def __init__(self, telegram_id, field_name, value):
        self.telegram_id = telegram_id
        self.field_name = field_name
        self.value = value


def buttons_comp(user_telegram_id):
    buttons = set()
    for computer in Computer.select().join(User).where(User.telegram_id == user_telegram_id):
        buttons.add(computer.computer_name)
    return buttons


# поведение при команде /start
@bot.message_handler(content_types=['text'])
def start_message(message):
    # проверка первого запуска и отправка инструкции
    if checking_records() and check_user_in_users(message.chat.id) and message.text == '/start':
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(*buttons)
        bot.send_message(message.chat.id, 'Приветствую, администратор! Какой компьютер хотите включить?',
                         reply_markup=keyboard)
    elif check_user_in_users(message.chat.id) and message.text in (buttons_comp(message.chat.id)):
        keyboard = telebot.types.ReplyKeyboardMarkup()
        buttons = buttons_comp(message.chat.id)
        keyboard.row(*buttons)
        computer = Computer.select().join(User).where(Computer.computer_name == message.text, User.telegram_id == message.chat.id).first() # проверить на баги
        send_magic_packet(computer.mac_address, ip_address=computer.ip_address,
                            port=computer.port)
        bot.send_message(message.chat.id, 'сейчас будет ;)', reply_markup=keyboard)
    elif checking_records() is False and message.text == '/start':
        bot.send_message(message.chat.id, 'Приветствую, это первый запуск telegrambot_wol.\nДавайте проведем '
                                          'первоначальную настройку. \nВаш id: ' + str(message.chat.id)
                         + '\nХотите его сохранить, как id администратора, и начать настройку?',
                         reply_markup=keyboard1)
        registration_values = set()
        registration_values.add(TempRegistrationField(message.chat.id, 'telegram_id', message.chat.id))
        bot.register_next_step_handler(message, registration, registration_values)


def registration(message, registration_values):
    if message.text == YES_MSG:
        bot.send_message(message.chat.id, 'Хорошо, тогда начнем.\nКак вы хотите, чтобы я к вам обращался?',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, retrieve_user_name, registration_values)


def retrieve_user_name(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'user_name', message.text))
    bot.send_message(message.chat.id, 'Принято!\nТеперь нужно указать MAC address Вашего компьютера')
    bot.register_next_step_handler(message, retrieve_mac_address, registration_values)


def retrieve_mac_address(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'mac_address', message.text))
    bot.send_message(message.chat.id, 'Теперь, укажите ip address вашего ПК в локальной сети, или Broadcast '
                                      'вашей локальной сети. Например, если адрес вашего роутера 192.168.1.1 '
                                      'то Broadcast будет 192.168.1.255. Если не хотите заморачиваться,'
                                      ' можно просто указать ip address вашего ПК :). Узнать его можно,'
                                      ' введя в командную строку вашего ПК команду:\nipconfig')
    bot.register_next_step_handler(message, retrieve_ip_address, registration_values)


def retrieve_ip_address(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'ip_address', message.text))
    bot.send_message(message.chat.id, 'Теперь, укажите порт вашего пк. '
                                      'Это порт на который приходит "магический пакет" он же "Wake on LAN", '
                                      'в большинстве случаев равен 9 или 7')
    bot.register_next_step_handler(message, retrieve_port, registration_values)


def retrieve_port(message, registration_values):
    registration_values.add(TempRegistrationField(message.chat.id, 'port', message.text))
    bot.send_message(message.chat.id, 'Ну а теперь, укажите, как будет называться ваш ПК в кнопках бота :)')
    bot.register_next_step_handler(message, retrieve_computer_name, registration_values)


def retrieve_computer_name(message, registration_values):
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

    bot.send_message(message.chat.id, 'Настройка завершена!\n'
                                      f'Ваш id telegram: {telegram_id}\n'
                                      f'Ваше имя: {user_name}\n'
                                      f'Имя вашего ПК: {computer_name}\n'
                                      f'MAC address: {mac_address}\n'
                                      f'IP address: {ip_address}\n'
                                      f'Port: {port}\n'
                                      'Все верно? ', reply_markup=keyboard1)
    bot.register_next_step_handler(message, save_registration, telegram_id, user_name, computer_name, mac_address,
                                   ip_address, port)


def save_registration(message, telegram_id, user_name, computer_name, mac_address, ip_address, port):
    if message.text == YES_MSG:
        if telegram_id == message.chat.id:
            users_str = User(telegram_id=telegram_id, user_name=user_name, admin=1)
            computer_str = Computer(user_id=users_str, computer_name=computer_name, mac_address=mac_address,
                                    ip_address=ip_address, port=port)
            users_str.save()
            computer_str.save()
            bot.send_message(message.chat.id, 'Изменения сохранены!', reply_markup=types.ReplyKeyboardRemove())


# метод связи с API Telegram
# цикл, чтобы бот не падал при отключении интернета
while True:
    try:
        bot.polling(none_stop=True)
    except Exception:
        sleep(1)
