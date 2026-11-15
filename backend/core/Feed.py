#Логика обработки ленты с рецептами
# Система рекомендаций будет основана на векторах и их скалярных произведений
# каждый вектор это основной компонент блюда, например вектор курицы, свинины,
# рыба и тд, в начале при регистрации пользователь выбирает любимые ингредиенты,
# к примеру пользователь выбрал мясо, значит вектор с мясом будет больше чем остальные,
# если пользователь ничего не выбрал то все вектора будут равны друг другу, например 5,
# когда пользователь будет лайкать несколько раз подряд блюдо в котором содержится мясо,
# то соответствующий вектор будет увеличиваться, в случае с дизлайками уменьшаться.
# на основе этих величин векторов будет выстраиваться лента.


class FeedService: 

    def __init__(self, db_manager):
        self.db = db_manager

    async def get_feed(self, session, user_id: int, limit: int = 200) -> list[dict]:
        """
        Функция генерации ленты рекомендаций пользователя
        """

        dishes = await self.db.get_candidate_dishes(session, user_id, limit)
        if not dishes:
            return []

        user_vector_obj = await self.db.get_user_vector(session, user_id)
        user_vector = user_vector_obj.root

        scored_dishes = []
        for dish in dishes: 
            score = 0.0

            for tag in dish["tags"]:
                tag_name = tag["name"]

                weight = user_vector.get(tag_name, 5.0)
                score += weight

            dish["relevance_score"] = score
            scored_dishes.append(dish)

        scored_dishes.sort(key=lambda x: x["relevance_score"], reverse=True)
        scored_dishes = scored_dishes[:20]

        return scored_dishes