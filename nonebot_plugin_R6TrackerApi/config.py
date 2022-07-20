from pydantic import BaseSettings


class Config(BaseSettings):
    #标识
    at_flag = False
    use_cache_flag = False

    class Config:
        extra = "ignore"