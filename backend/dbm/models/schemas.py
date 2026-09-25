from pydantic import BaseModel, ConfigDict, RootModel

class TagsShema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class DishesSchema(BaseModel):
    id: int
    name: str

    tags: list[TagsShema] = []

    model_config = ConfigDict(from_attributes=True)

class UserVectorSchema(RootModel[dict[str, float]]):
    pass