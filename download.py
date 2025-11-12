from typing import Type, TypeVar, List, Protocol, ClassVar
import datetime
from schemas import WBSale, WBStock, APIEndpoint

import asyncio
import aiosqlite
import httpx
from icecream import ic
from pydantic import BaseModel

DB = "wb.db"
API_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjIsImVudCI6MSwiZXhwIjoxNzc3NTkzOTkxLCJpZCI6IjAxOWEzNTAzLTJjMzctN2E0Ni1iMmE4LTkwNzQyY2I0Y2QwNyIsImlpZCI6MTI0NTM4NzAsIm9pZCI6MTU2OTMsInMiOjAsInNpZCI6ImZmYTA4MmZiLWUxZTktNTdhYi05ZWQyLWM2ZjE3ZDNhZWZkYSIsInQiOnRydWUsInVpZCI6MTI0NTM4NzB9.Mqq4xLDKhdZ_92ptEWiQsK7gepAX1coB39eHcqqBIYuZXpCjbnj4ozVSsR2ENXRGVKxTzlwmLz3x1VRla2Wxkg"
BASE_URL = "https://statistics-api-sandbox.wildberries.ru/api/v1/supplier"

HEADERS = {
    "Authorization": API_TOKEN
}

async def create_tables():
    """Create database tables from schema.sql"""
    async with aiosqlite.connect(DB) as db:
        with open("schema.sql", "r") as f:
            sql_script = f.read()
        await db.executescript(sql_script)
        await db.commit()

async def ping():
    """
    Fetch stocks data from Wildberries API.
    You need to confirm the exact endpoint and parameters[citation:4].
    """
    from icecream import ic
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://statistics-api-sandbox.wildberries.ru/ping", headers=HEADERS)
            global r
            r = response
            ic(response.json())
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            ic(e)

# class APIEndpoint(Protocol):
#     _url: ClassVar[str]
#     _method: ClassVar[str]

ModelType = TypeVar('ModelType', bound=APIEndpoint)
async def query_api(client: httpx.AsyncClient, endpoint: str, params: dict, ModelClass: Type[APIEndpoint], base_url: str = BASE_URL) -> List[ModelType]:
    """
    Делает запрос к API

    :param endpoint: Эндпоинт API
    :param params: Параметры для тела запроса к API
    :param ModelClass: Модель для валидации
    """
    try:
        response = await client.request(
            url=ModelClass._url,
            method=ModelClass._method,
            headers=HEADERS,
            data=params # ?
        )
        # response = await client.get(f"{base_url}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return [ModelClass(**item) for item in data]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("X-Ratelimit-Retry", 5))
            print(f"Rate limit hit. Retrying after {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            return await query_api(client, endpoint, params, ModelClass)
    except Exception as e:
        ic(response.json())
        raise e

async def get_all_with_pagination(kind_of_data: str, date_from: datetime, date_to: datetime) -> List[ModelType]:
    """
    Собирает все данные в промежутке

    :param kind_of_data: sales или stocks
    :param date_from: с какой даты смотреть
    :param date_to: по какую дату
    """
    assert kind_of_data in ["sales", "stocks"]
    # assert date_from.tzinfo is not None
    # assert date_to.tzinfo is not None

    response = 1
    lastChangeDate = date_from
    data = []
    async with httpx.AsyncClient() as client:
        while response != [] and lastChangeDate < date_to:
            response = await query_api(client, kind_of_data, params={"dateFrom": lastChangeDate.isoformat()}, ModelClass=WBSale if "sales" else WBStock)
            if response == []:
                break
            data.extend(response)
            lastChangeDate = response[-1].lastChangeDate.replace(tzinfo=None)
    return data

async def save_to_db(table: str, data: List[Type[BaseModel]]):
    """Save data to table"""
    # Автоматически получаем поля из модели
    fields = list(data[0].model_dump().keys())
    columns = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    values = [tuple(item.model_dump()[field] for field in fields) for item in data]

    async with aiosqlite.connect(DB) as db:
        await db.executemany(
            f"INSERT INTO sales ({columns}) VALUES ({placeholders})",
            values
        )
        await db.commit()

async def main():
    """Main function to run the data pipeline"""
    # await ping()

    data = await get_all_with_pagination(
        "sales",  
        date_from=datetime.datetime.now() - datetime.timedelta(days=365*3), 
        date_to=datetime.datetime.now())
    ic(data[-1])
    await save_to_db("sales", data)

if __name__ == "__main__":
    asyncio.run(main())
