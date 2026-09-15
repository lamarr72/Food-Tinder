# импорт движка (подключение к бд) + базовый класс + все модели (для SQLAlchemy)
from backend.dbm.database import engine
from backend.dbm.models.base import Base
from backend.dbm.models.core_models import User, Dish, Swipe, Tag, RationItem, dish_tags

def create_tables():
    print("Connecting to DB and creating tables...")

    #перевод классов в SQL и отправка в PostgreSQL
    Base.metadata.create_all(bind=engine)

    print("The tables was created")

if __name__ == "__main__":
    create_tables()