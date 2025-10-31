from typing import Type, TypeVar, List

# from schemas import WBSale, WBStock

import asyncio
import aiosqlite
import httpx
from icecream import ic
from pydantic import BaseModel

DB = "wildberries.db"
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
            response = await client.get(f"{BASE_URL}/ping", headers=HEADERS)
            global r
            r = response
            ic(response.json())
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            ic(e)

ModelType = TypeVar('ModelType', bound=BaseModel)
async def query_api(client: httpx.AsyncClient, endpoint: str, params: dict, ModelClass: Type[BaseModel]) -> List[ModelType]:
    """
    Делает запрос к API

    :param endpoint: Эндпоинт API
    :param params: Параметры для тела запроса к API
    :param ModelClass: Модель для валидации
    """
    try:
        response = await client.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return [ModelClass(**item) for item in data]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("X-Ratelimit-Retry", 5))
            print(f"Rate limit hit. Retrying after {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            return await query_api(client, params, ModelClass)
    except Exception as e:
        ic(response.json())
        raise e

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
    await create_tables()

    # Use a recent date; format might need adjustment[citation:7]
    # date_from = "2023-10-01"

    # print("Fetching sales data...")
    # sales = await fetch_sales(date_from)
    # if sales:
    #     await save_sales_to_db(sales)
    #     print(f"Successfully saved {len(sales)} sales records.")
    # else:
    #     print("Failed to fetch sales data.")

    # print("Fetching stocks data...")
    # stocks = await fetch_stocks(date_from)
    # if stocks:
    #     await save_stocks_to_db(stocks)
    #     print(f"Successfully saved {len(stocks)} stock records.")
    # else:
    #     print("Failed to fetch stocks data.")

if __name__ == "__main__":
    asyncio.run(main())
