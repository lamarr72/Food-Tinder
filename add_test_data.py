import asyncio
from datetime import date
from sqlalchemy import insert
from backend.dbm.database import SessionLocal
from backend.dbm.models.core_models import (
    User, Tag, Ingredient, Dish, DishImage, RecipeStep, Swipe, RationItem,
    dish_tags, dish_ingredients, user_unwanted_ingredients,
    ReactionType, MealType
)

async def add_test_data():
    async with SessionLocal() as db:
        try:
            # Тестовый пользователь Ирина
            new_user = User(
                email="irina@test.ru",
                hashed_password="fake_hashed_password_123",
                session_id="session_irina_001",
                name="Ирина",
                gender="female",
                avatar_url="/static/images/avatars/irina.jpg",
                birth_date=date(2002, 2, 16),
                height=170,
                weight=65.0
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            # Справочник ингредиентов
            ingredients_names = [
                "Яйцо куриное", "Персик", "Клубника", "Сливочное масло",
                "Овсяные хлопья", "Молоко", "Банан", "Куриное филе",
                "Рис", "Брокколи", "Оливковое масло", "Лосось",
                "Авокадо", "Творожный сыр", "Хлеб цельнозерновой",
                "Творог", "Сметана", "Мука", "Говядина", "Свекла",
                "Картофель", "Капуста", "Греческий йогурт", "Мед", "Грецкий орех",
                "Помидор", "Огурец", "Сыр фета"
            ]
            ingr_map = {}
            for name in ingredients_names:
                ingr = Ingredient(name=name)
                db.add(ingr)
                ingr_map[name] = ingr
            await db.commit()
            for ingr in ingr_map.values():
                await db.refresh(ingr)

            # Аллергии / Нежелательные продукты
            await db.execute(insert(user_unwanted_ingredients).values([
                {"user_id": new_user.id, "ingredient_id": ingr_map["Персик"].id},
                {"user_id": new_user.id, "ingredient_id": ingr_map["Клубника"].id},
            ]))

            # Справочник тегов
            tags_names = [
                "Завтрак", "Обед", "Ужин", "Перекус",
                "Высокий белок", "Вегетарианское", "ПП", "Рыба", "Мясо", "Суп", "Быстрое"
            ]
            tag_map = {}
            for name in tags_names:
                t = Tag(name=name)
                db.add(t)
                tag_map[name] = t
            await db.commit()
            for t in tag_map.values():
                await db.refresh(t)

            # Набор разнообразных блюд
            dishes_data = [
                {
                    "name": "Идеальный скрэмбл",
                    "description": "Нежные, кремовые яйца на сливочном масле.",
                    "price": 120, "calories": 318, "proteins": 21.0, "fats": 24.0, "carbs": 2.0,
                    "cooking_time": 10, "difficulty": 1, "equipment": "Сковорода", "rating": 5.0,
                    "tags": ["Завтрак", "Высокий белок", "Быстрое"],
                    "ingredients": [("Яйцо куриное", 3.0, "шт"), ("Сливочное масло", 15.0, "г")],
                    "images": ["/static/images/scramble_1.jpg", "/static/images/scramble_2.jpg"],
                    "steps": [
                        (1, "Слегка взбить яйца вилкой до однородности.", "/static/images/step_1.jpg"),
                        (2, "Растопить сливочное масло на слабом огне и влить яйца, постоянно помешивая.", None)
                    ]
                },
                {
                    "name": "Овсяная каша с бананом и медом",
                    "description": "Питательный классический завтрак с медленными углеводами.",
                    "price": 90, "calories": 340, "proteins": 10.5, "fats": 6.2, "carbs": 60.0,
                    "cooking_time": 15, "difficulty": 1, "equipment": "Кастрюля", "rating": 4.7,
                    "tags": ["Завтрак", "Вегетарианское", "ПП"],
                    "ingredients": [
                        ("Овсяные хлопья", 60.0, "г"), ("Молоко", 200.0, "мл"),
                        ("Банан", 1.0, "шт"), ("Мед", 15.0, "г")
                    ],
                    "images": ["/static/images/oatmeal_1.jpg"],
                    "steps": [
                        (1, "Засыпать хлопья в кипящее молоко и варить 10 минут.", None),
                        (2, "Украсить нарезанным бананом и полить медом.", None)
                    ]
                },
                {
                    "name": "Тост с авокадо и лососем",
                    "description": "Хрустящий цельнозерновой хлеб с творожным сыром и слабосоленой рыбой.",
                    "price": 320, "calories": 380, "proteins": 18.0, "fats": 22.0, "carbs": 28.0,
                    "cooking_time": 10, "difficulty": 1, "equipment": "Тостер", "rating": 4.9,
                    "tags": ["Завтрак", "Перекус", "Рыба", "Быстрое"],
                    "ingredients": [
                        ("Хлеб цельнозерновой", 2.0, "шт"), ("Творожный сыр", 40.0, "г"),
                        ("Авокадо", 0.5, "шт"), ("Лосось", 60.0, "г")
                    ],
                    "images": ["/static/images/avocado_toast.jpg"],
                    "steps": [
                        (1, "Подсушить хлеб в тостере и намазать творожным сыром.", None),
                        (2, "Выложить сверху ломтики авокадо и слабосоленого лосося.", None)
                    ]
                },
                {
                    "name": "Куриное филе с рисом и брокколи",
                    "description": "Сбалансированный обед для поддержания формы.",
                    "price": 240, "calories": 450, "proteins": 42.0, "fats": 9.0, "carbs": 48.0,
                    "cooking_time": 30, "difficulty": 2, "equipment": "Сковорода, Кастрюля", "rating": 4.6,
                    "tags": ["Обед", "Ужин", "Высокий белок", "Мясо", "ПП"],
                    "ingredients": [
                        ("Куриное филе", 180.0, "г"), ("Рис", 80.0, "г"),
                        ("Брокколи", 100.0, "г"), ("Оливковое масло", 10.0, "мл")
                    ],
                    "images": ["/static/images/chicken_rice.jpg"],
                    "steps": [
                        (1, "Отварить рис и брокколи в подсоленной воде.", None),
                        (2, "Обжарить нарезанное филе на оливковом масле до золотистой корочки.", None)
                    ]
                },
                {
                    "name": "Запеченный стейк из лосося",
                    "description": "Сочная красная рыба, запеченная в духовке с капелькой масла.",
                    "price": 550, "calories": 410, "proteins": 36.0, "fats": 28.0, "carbs": 2.0,
                    "cooking_time": 25, "difficulty": 2, "equipment": "Духовка", "rating": 5.0,
                    "tags": ["Ужин", "Рыба", "Высокий белок", "ПП"],
                    "ingredients": [
                        ("Лосось", 200.0, "г"), ("Оливковое масло", 10.0, "мл"), ("Брокколи", 120.0, "г")
                    ],
                    "images": ["/static/images/baked_salmon.jpg"],
                    "steps": [
                        (1, "Разогреть духовку до 190 градусов.", None),
                        (2, "Сбрызнуть рыбу и брокколи маслом и запекать 20 минут.", None)
                    ]
                },
                {
                    "name": "Домашние сырники со сметаной",
                    "description": "Нежные творожные сырники с румяной корочкой.",
                    "price": 160, "calories": 390, "proteins": 26.0, "fats": 18.0, "carbs": 30.0,
                    "cooking_time": 20, "difficulty": 3, "equipment": "Сковорода", "rating": 4.8,
                    "tags": ["Завтрак", "Высокий белок", "Вегетарианское"],
                    "ingredients": [
                        ("Творог", 200.0, "г"), ("Яйцо куриное", 1.0, "шт"),
                        ("Мука", 30.0, "г"), ("Сметана", 40.0, "г")
                    ],
                    "images": ["/static/images/syrniki.jpg"],
                    "steps": [
                        (1, "Смешать творог, яйцо и муку, сформировать шайбочки.", None),
                        (2, "Обжарить с двух сторон под крышкой и подавать со сметаной.", None)
                    ]
                },
                {
                    "name": "Классический борщ с говядиной",
                    "description": "Наваристый свекольный суп со свежей капустой и сметаной.",
                    "price": 210, "calories": 280, "proteins": 19.0, "fats": 12.0, "carbs": 24.0,
                    "cooking_time": 60, "difficulty": 4, "equipment": "Кастрюля, Сковорода", "rating": 4.9,
                    "tags": ["Обед", "Суп", "Мясо"],
                    "ingredients": [
                        ("Говядина", 150.0, "г"), ("Свекла", 100.0, "г"),
                        ("Картофель", 100.0, "г"), ("Капуста", 80.0, "г"), ("Сметана", 30.0, "г")
                    ],
                    "images": ["/static/images/borscht.jpg"],
                    "steps": [
                        (1, "Сварить бульон из говядины, добавить картофель и капусту.", None),
                        (2, "Добавить тушеную свеклу, проварить 10 минут и подавать со сметаной.", None)
                    ]
                },
                {
                    "name": "Греческий салат с фетой",
                    "description": "Свежие овощи, кубики сыра фета и заправка из оливкового масла.",
                    "price": 190, "calories": 230, "proteins": 7.5, "fats": 18.0, "carbs": 9.0,
                    "cooking_time": 10, "difficulty": 1, "equipment": "Салатник", "rating": 4.7,
                    "tags": ["Ужин", "Перекус", "Вегетарианское", "ПП", "Быстрое"],
                    "ingredients": [
                        ("Помидор", 120.0, "г"), ("Огурец", 100.0, "г"),
                        ("Сыр фета", 60.0, "г"), ("Оливковое масло", 15.0, "мл")
                    ],
                    "images": ["/static/images/greek_salad.jpg"],
                    "steps": [
                        (1, "Крупно нарезать помидоры и огурцы.", None),
                        (2, "Выложить сверху кубики феты и полить оливковым маслом.", None)
                    ]
                },
                {
                    "name": "Фруктовый боул с клубникой и персиком",
                    "description": "Тестовое блюдо с аллергенами Ирины (должно автоматически отсекаться в её ленте!).",
                    "price": 220, "calories": 260, "proteins": 9.0, "fats": 10.0, "carbs": 34.0,
                    "cooking_time": 5, "difficulty": 1, "equipment": "Миска", "rating": 4.5,
                    "tags": ["Завтрак", "Перекус", "Вегетарианское", "Быстрое"],
                    "ingredients": [
                        ("Греческий йогурт", 150.0, "г"), ("Клубника", 80.0, "г"),
                        ("Персик", 1.0, "шт"), ("Грецкий орех", 20.0, "г")
                    ],
                    "images": ["/static/images/fruit_bowl.jpg"],
                    "steps": [
                        (1, "Выложить йогурт в миску и украсить нарезанными фруктами и орехами.", None)
                    ]
                }
            ]

            created_dishes = []
            for d_info in dishes_data:
                dish = Dish(
                    name=d_info["name"],
                    description=d_info["description"],
                    price=d_info["price"],
                    calories=d_info["calories"],
                    proteins=d_info["proteins"],
                    fats=d_info["fats"],
                    carbs=d_info["carbs"],
                    cooking_time=d_info["cooking_time"],
                    difficulty=d_info["difficulty"],
                    equipment=d_info["equipment"],
                    rating=d_info["rating"],
                    author_id=new_user.id,
                    is_public=True
                )
                db.add(dish)
                await db.commit()
                await db.refresh(dish)
                created_dishes.append(dish)

                # Привязка тегов
                await db.execute(insert(dish_tags).values([
                    {"dish_id": dish.id, "tag_id": tag_map[t_name].id}
                    for t_name in d_info["tags"]
                ]))

                # Привязка ингредиентов
                await db.execute(insert(dish_ingredients).values([
                    {
                        "dish_id": dish.id,
                        "ingredient_id": ingr_map[i_name].id,
                        "quantity": qty,
                        "unit": unit
                    }
                    for i_name, qty, unit in d_info["ingredients"]
                ]))

                # Добавление изображений
                for img_url in d_info["images"]:
                    db.add(DishImage(dish_id=dish.id, image_url=img_url))

                # Добавление шагов рецепта
                for step_num, desc, step_img in d_info["steps"]:
                    db.add(RecipeStep(
                        dish_id=dish.id,
                        step_number=step_num,
                        description=desc,
                        image_url=step_img
                    ))

            # Стартовый рацион на день 1
            ration_breakfast = RationItem(
                user_id=new_user.id,
                dish_id=created_dishes[0].id,  #идеальный скрэмбл
                meal_type=MealType.BREAKFAST,
                day_number=1,
                portion_grams=150
            )
            db.add(ration_breakfast)

            await db.commit()
            print("Успех! Тестовый профиль Ирины и 9 блюд загружены.")

        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(add_test_data())