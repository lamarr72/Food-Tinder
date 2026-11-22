# считает КБЖУ и цену с учетом реального веса порции (portion_grams / 100), группирует по дням и делает автоподбор рациона
import random
from sqlalchemy.ext.asyncio import AsyncSession
from dbm.models.core_models import MealType

# соответствие типа приема пищи и тега в БД
MEAL_TO_TAG = {
    MealType.BREAKFAST: "Завтрак",
    MealType.LUNCH: "Обед",
    MealType.DINNER: "Ужин",
    MealType.SNACK: "Перекус",
}


class RationService:
    """
    логика конструктора рациона: подсчет КБЖУ/цены и автоподбор
    """

    def __init__(self, ration_manager):
        self.db = ration_manager

    async def get_full_ration(self, session: AsyncSession, user_id: int) -> dict:
        items = await self.db.get_ration_items(session, user_id)

        days = {}
        total_stats = {"calories": 0.0, "proteins": 0.0, "fats": 0.0, "carbs": 0.0, "price": 0.0}

        for item in items:
            day_num = item["day_number"]
            factor = item["portion_grams"] / 100.0
            dish = item["dish"]

            item_stats = {
                "calories": round(dish["calories"] * factor, 1),
                "proteins": round(dish["proteins"] * factor, 1),
                "fats": round(dish["fats"] * factor, 1),
                "carbs": round(dish["carbs"] * factor, 1),
                "price": round(dish["price"] * factor, 2),
            }

            if day_num not in days:
                days[day_num] = {
                    "day_number": day_num,
                    "items": [],
                    "stats": {"calories": 0.0, "proteins": 0.0, "fats": 0.0, "carbs": 0.0, "price": 0.0}
                }

            days[day_num]["items"].append({
                "id": item["id"],
                "meal_type": item["meal_type"],
                "portion_grams": item["portion_grams"],
                "dish_id": dish["id"],
                "dish_name": dish["name"],
                "stats": item_stats
            })

            for key in total_stats:
                days[day_num]["stats"][key] = round(days[day_num]["stats"][key] + item_stats[key], 2)
                total_stats[key] = round(total_stats[key] + item_stats[key], 2)

        return {
            "days": [days[d] for d in sorted(days.keys())],
            "total": total_stats
        }

    async def auto_generate_ration(
        self,
        session: AsyncSession,
        user_id: int,
        days_count: int = 3,
        meals: list[MealType] | None = None
    ) -> dict:
        """
        автоматически собирает рацион на N дней из избранных/лайкнутых блюд
        """
        days_count = max(1, min(days_count, 14))
        if not meals:
            meals = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]

        candidates = await self.db.get_favorite_dishes(session, user_id)
        if not candidates:
            return {"days": [], "total": {"calories": 0.0, "proteins": 0.0, "fats": 0.0, "carbs": 0.0, "price": 0.0}}

        await self.db.clear_ration(session, user_id)

        for day in range(1, days_count + 1):
            for meal in meals:
                target_tag = MEAL_TO_TAG.get(meal)
                matching = [d for d in candidates if target_tag in d["tags"]]
                pool = matching if matching else candidates
                chosen = random.choice(pool)

                await self.db.add_ration_item(
                    session=session,
                    user_id=user_id,
                    dish_id=chosen["id"],
                    meal_type=meal,
                    day_number=day,
                    portion_grams=100
                )

        return await self.get_full_ration(session, user_id)