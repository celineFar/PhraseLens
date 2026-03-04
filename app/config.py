from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://content_search:content_search@db:5432/content_search"
    data_dir: str = "/app/data"
    chunk_size: int = 5  # number of lines per passage
    spacy_model: str = "en_core_web_sm"

    model_config = {"env_file": ".env"}


settings = Settings()
