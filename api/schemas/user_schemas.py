from pydantic import BaseModel, ConfigDict, field_validator


class UserBase(BaseModel):
    pass



class UserCreate(UserBase):
    app_id: str
    name: str | None = None
    email: str | None = None
    password: str

    @field_validator("email")
    @classmethod
    def empty_str_to_none(cls, value: str | None) -> str | None:
        if value is not None and value.strip() == "":
            return None
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    app_id: str
    name: str | None
    email: str | None


class UserLogin(UserBase):
    identifier: str
    password: str
