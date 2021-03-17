import peewee


db = peewee.SqliteDatabase('telegrambot_wol.sqlite')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    id = peewee.AutoField(column_name='id')
    telegram_id = peewee.IntegerField(column_name='telegram_id')
    user_name = peewee.CharField(column_name='user_name')
    admin = peewee.BooleanField(column_name='admin')

    class Meta:
        table_name = 'User'


class Computer(BaseModel):
    id = peewee.AutoField(column_name='id')
    user_id = peewee.ForeignKeyField(User, related_name='owner')
    computer_name = peewee.CharField(column_name='computer_name')
    mac_address = peewee.CharField(column_name='mac_address')
    ip_address = peewee.CharField(column_name='ip_address')
    port = peewee.IntegerField(column_name='port')

    class Meta:
        table_name = 'Computer'


