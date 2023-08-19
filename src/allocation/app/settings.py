import os
from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict

if os.path.exists(".venv"):
    ENV_FILE = ".venv"
else:
    ENV_FILE = "/.venv"


class Settings(BaseSettings):
    db_hostname: str
    db_port: int
    db_root_password: str
    db_user_name: str
    db_name: str
    db_test_name: str

    redis_host: str
    redis_port: int

    api_host: str
    api_port: int

    email_host: str = "localhost"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    def get_edgedb_dsn(self, *, test_db: bool = False) -> str:
        db_name = self.db_name if not test_db else self.db_test_name
        return f"edgedb://{0}:{1}@{2}:{3}/{4}".format(
            self.db_user_name,
            self.db_root_password,
            self.db_hostname,
            self.db_port,
            db_name,
        )

    def get_api_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    def get_redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    def get_email_host_and_port(self):
        host = self.email_host
        port = 11025 if host == "localhost" else 1025
        http_port = 18025 if host == "localhost" else 8025
        return dict(host=host, port=port, http_port=http_port)


@cache
def get_settings() -> Settings:
    return Settings()  # noqa


settings = get_settings()
