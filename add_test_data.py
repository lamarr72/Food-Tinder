from sqlalchemy import insert
from backend.dbm.database import SessionLocal
from backend.dbm.models.core_models import User, Dish, Tag, dish_tags

def add_test_data():
    #открытие сессии к бд
    db = SessionLocal()
    
    try:
        # создание тестового пользователя
        new_user = User(
            email="test.test@test.ru",
            session_id="test_session_67"
        )
        db.add(new_user)
        db.commit() 
        #обновление объекта, чтобы SQLAlchemy подтянула сгенерированный базой id
        db.refresh(new_user) 
        
        #создание тестовых тегов
        tag_breakfast = Tag(name="Завтрак")
        tag_protein = Tag(name="Высокий белок")
        db.add_all([tag_breakfast, tag_protein])
        db.commit()
        db.refresh(tag_breakfast)
        db.refresh(tag_protein)
        
        #добавление блюда 
        scramble = Dish(
            name="Идеальный скрэмбл",
            description="Нежные, кремовые яйца на сливочном масле.",
            price=0,  #домашнее блюдо
            calories=318,
            proteins=21.0,
            fats=24.0,
            carbs=2.0,
            ingredients="Яйца - 3 шт., Сливочное масло - 15 г., Соль по вкусу.",
            recipe="1. Слегка взбить яйца.\n2. Растопить масло на слабом огне.\n3. Влить яйца и постоянно помешивать лопаткой.\n4. Снять с огня, пока они еще слегка влажные.",
            author_id=new_user.id,  #привязка авторства
            is_public=True
        )
        db.add(scramble)
        db.commit()
        db.refresh(scramble)

        #связка блюда с тегами через промежуточную таблицу dish_tags
        #тк это объект Table, используется прямая команда insert
        db.execute(insert(dish_tags).values([
            {"dish_id": scramble.id, "tag_id": tag_breakfast.id},
            {"dish_id": scramble.id, "tag_id": tag_protein.id}
        ]))
        db.commit()

        print("The test profile and recipe have been added to the database.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_data()