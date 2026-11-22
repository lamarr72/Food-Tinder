from pydantic import BaseModel, ConfigDict, RootModel


class TagSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# алиас на случай, если где-то в других ветках остался старый импорт
TagsShema = TagSchema


class DishImageSchema(BaseModel):
    id: int
    image_url: str

    model_config = ConfigDict(from_attributes=True)


class RecipeStepSchema(BaseModel):
    step_number: int
    description: str
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DishIngredientSchema(BaseModel):
    id: int
    name: str
    quantity: float
    unit: str


class DishesSchema(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: int | None = None
    calories: int | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None
    cooking_time: int = 0
    difficulty: int = 1
    equipment: str | None = None
    rating: float = 0.0

    tags: list[TagSchema] = []
    images: list[DishImageSchema] = []
    steps: list[RecipeStepSchema] = []
    ingredients: list[DishIngredientSchema] = []

    model_config = ConfigDict(from_attributes=True)


class UserVectorSchema(RootModel[dict[str, float]]):
    pass