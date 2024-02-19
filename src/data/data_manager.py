import json
import os

class DataManager:
    def __init__(self) -> None:
        ...

    @staticmethod
    def validate_data() -> bool:
        with open("src/data/rosec.json", "r") as data:
            parsed = json.load(fp=data)
        return bool(parsed[".ROBLOSECURITY"])

    @staticmethod
    def get_data() -> bool:
        with open("src/data/rosec.json", "r") as data:
            parsed = json.load(fp=data)
        return parsed

    @staticmethod
    def store_data(key: str, value: str | int | float) -> bool:
        with open("src/data/rosec.json", "r") as data:
            parsed = json.load(fp=data)
            parsed[key] = value

        with open("src/data/rosec.json", "w") as storage:
            parsed = json.dumps(parsed)
            storage.write(parsed)