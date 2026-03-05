from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Local-first defaults; docker-compose overrides these with container values.
    database_url: str = "postgresql://content_search:content_search@localhost:5432/content_search"
    data_dir: str = "./data"
    chunk_size: int = 5  # number of lines per passage
    spacy_model: str = "en_core_web_sm"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_dir: str = "./chroma_data"

    model_config = {"env_file": ".env"}


settings = Settings()
