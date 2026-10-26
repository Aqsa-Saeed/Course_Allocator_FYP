from pydantic import BaseModel, Field, field_validator


class ForgotPasswordRequest(BaseModel):
    username: str = Field(min_length=1, max_length=150)


class ResetPasswordRequest(BaseModel):
    username: str = Field(min_length=1, max_length=150)
    code: str = Field(min_length=1, max_length=12)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def fits_bcrypt(cls, value: str) -> str:
        # bcrypt only uses the first 72 bytes; refuse longer input instead of silently cutting it.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (72 bytes maximum).")
        return value


class MessageOut(BaseModel):
    message: str
