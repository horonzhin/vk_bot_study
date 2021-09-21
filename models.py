from pony.orm import Database, Required, Json

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


# класс отвечающий за находение пользователя на каком-то шаге какого-то сценария. Сохраняется в бд для того,
# чтобы при перезапуске бота данные не сбрасывались.
class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    # добавляем user_id и делаем его уникальным, чтобы ID у каждого пользователя был свой. И при попытке одновременной
    # записи (при мультипоточке) в один и тот же ID вылетит ошибка на одном из них.
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """Заявка на регистрацию"""
    name = Required(str)
    email = Required(str)


db.generate_mapping(create_tables=True)

# psql -U postgres - войти в пользователя
# \! chcp 1251 - установить кодировку для винды
# psql -d vk_chat_bot - создать базу
# \c vk_chat_bot - зайти в базу
# \dt - посмотреть таблицы в базе
# select * from userstate; - зайти в таблицу
# drop table userstate; - удалить таблицу






