import configparser
import telebot
from wakeonlan import send_magic_packet


# работа с файлами settings и token
config = configparser.ConfigParser()  # создаём объекта парсера
config.read('settings.ini')     # читаем настройки
config.read("token.ini")    # читаем токен

# подключение токена
bot = telebot.TeleBot(config['Token']['token'])

# включение кнопок клавиатуры в боте
keyboard1 = telebot.types.ReplyKeyboardMarkup()
keyboard2 = telebot.types.ReplyKeyboardMarkup()
keyboard1.row('да', 'нет')
keyboard2.row('включи компьютер', 'проверка работы бота')


# поведение при команде /start
@bot.message_handler(commands=['start'])
def start_message(message):
    if config['telegrambotWOL']['user'] == '0':     # проверка первого запуска и отправка инструкции
        bot.send_message(message.chat.id, 'Приветствую, это первый запуск telegrambotWOL \nВаш id: ' + str(
            message.chat.id) + '\nПожалуйста, укажите его в файле settings.ini, следуя примечаниям в файле, затем,'
                               ' перезапустите программу и отправьте команду\n /start')
        print('Приветствую, это первый запуск telegrambotWOL \nВаш id: ' + str(
            message.chat.id) + '\nПожалуйста, укажите его в файле settings.ini, следуя примечаниям в файле, затем,'
                               ' перезапустите программу и отправьте команду\n /start')
    elif str(message.chat.id) == config['telegrambotWOL']['user']:  # проверка на соответсвие id user
        bot.send_message(message.chat.id, 'Приветствую, администратор! Хотите включить компьтер?',
                         reply_markup=keyboard1)  # отправка сообщения в telegram
        print('обнаружен администратор: ' + str(message.chat.id))  # отправка id пользователя в консоль
    elif str(message.chat.id) != config['telegrambotWOL']['user']:  # проверка id администратора
        print('обнаружен неизвестный пользователь: ' + str(message.chat.id))    # отправка id пользователя в консоль


# поведение при ответах на команды
@bot.message_handler(content_types=['text'])
def send_text(message):
    if str(message.chat.id) == config['telegrambotWOL']['user']:    # проверка id администратора
        if message.text.lower() in ('включи компьютер', 'да'):
            bot.send_message(message.chat.id, 'сейчас будет ;)', reply_markup=keyboard2)
            send_magic_packet(config['telegrambotWOL']['mac_address'], ip_address=config['telegrambotWOL']['ip_address'],
                              port=int(config['telegrambotWOL']['port']))   # отправка пакета на включение PC
            print('пользователь ' + str(message.chat.id) + ' включил компьютер')
        elif message.text.lower() == 'нет':
            bot.send_message(message.chat.id, 'ну ладно :(', reply_markup=keyboard2)
        elif message.text.lower() == 'проверка работы бота':
            bot.send_message(message.chat.id, 'я тут!', reply_markup=keyboard2)
            print('бот работает успешно!')
    elif str(message.chat.id) != config['telegrambotWOL']['user']:  # проверка id администратора
        print('обнаружен неизвестный пользователь: ' + str(message.chat.id))


# метод связи с API Telegram
bot.polling()