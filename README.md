# telegrambotWOL
Это телеграмм-бот для удаленного запуска компьютера с помощью Wake-on-LAN. Может быть полезно тем, у кого нет возможности иметь статический IP-адрес, или если вы находитесь за NAT.

Как запустить:
1. Вам нужно иметь в этой сети какое-нибудь устройство на дистрибутиве Linux, или другой системе,
но с обязательно установленным Python 3. Устройство должно работать 24/7, чтобы оно в любой момент могло ответить на ваши запросы.
У меня например стоит на Raspberry Pi 1.
2. Скачиваете последнюю версию программы любым удобным способом.
На главной странице программы жмёте зелёную кнопку "Code" потом жмёте "download ZIP", после этого распаковываете папку telegrambotwol в удобное для вас место.
Потом ставите зависимости с помощью команды
pip install -r requirements.txt
Если не работает, напишите полный путь до файла, requirements.txt, который находится в папке telegrambotwol, пример
pip install -r /home/user/telegrambotwol/requirements.txt
3. Теперь нужно зарегистрировать бота в телеграмм
Для этого в Telegram существует специальный бот — @BotFather.
Пишем ему /start и получаем список всех его команд.
Первая и главная — /newbot — отправляем ему и бот просит придумать имя нашему новому боту. Единственное ограничение на имя — оно должно оканчиваться на «bot».
Следуйте его инструкциям, и в конце он должен дать вам токен доступа. Копируем его и добавляем в файл token.ini, вместо примера.
4. Теперь нужно настроить файл settings.ini, открыть его в блокноте, и прочитать комментарии, там написано, как его настроить.
5. Если вы все сделали правильно, поздравляю, можете запустить бота, введите команду
python3 telegrambot_wol.py
И пользуйтесь. Если не получилось, то зайдите в папку с этим файлом, и повторите снова. Например
cd /home/user/telegrambotWOL/
python3 telegrambot_wol.py
