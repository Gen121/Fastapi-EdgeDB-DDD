from functools import cache
from pydantic import ConfigDict

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_hostname: str
    db_port: int
    db_root_password: str
    db_user_name: str
    db_name: str
    db_test_name: str

    api_host: str
    api_port: int

    model_config = ConfigDict(env_file='.venv')

    def get_edgedb_dsn(self, *, test_db: bool = False) -> str:
        db_name = self.db_name if not test_db else self.db_test_name
        return f'edgedb://{self.db_user_name}:{self.db_root_password}@{self.db_hostname}:{self.db_port}/{db_name}'

    def get_api_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"


@cache
def get_settings() -> Settings:
    return Settings()  # noqa


settings = get_settings()
