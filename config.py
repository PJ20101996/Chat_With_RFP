from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_PORT: int
    MYSQL_PASSWORD: str
    MYSQL_USER: str
    MYSQL_DB: str
    MYSQL_HOST: str

    JWT_SECRET_KEY: str

    JWT_REFRESH_SECRET_KEY: str

    aws_access_key_id: str
    aws_secret_access_key: str
    region: str
    bucket: str

    email_lambda_arn: str
    je_lambda_arn: str
    db_lambda_arn: str
    open_ai_key: str

    class Config:
        env_file = './.env'

settings = Settings()