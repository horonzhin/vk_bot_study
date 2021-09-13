from pony.orm import Database, Required, Json

from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """Состояние пользователя внутри сценария"""
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)