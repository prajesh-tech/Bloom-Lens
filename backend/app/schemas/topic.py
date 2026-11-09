from pydantic import BaseModel, Field, field_validator


class TopicInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator('name', mode='before')
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class TopicResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    is_managed: bool
    model_config = {'from_attributes': True}
