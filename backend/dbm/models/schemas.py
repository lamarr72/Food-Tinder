from pydantic import BaseModel, ConfigDict

class TagsSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class DishesSchema(BaseModel):
    id: int
    name: str

    tags: list[TagsSchema] = []

    model_config = ConfigDict(from_attributes=True)

