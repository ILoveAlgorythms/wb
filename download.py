from typing import Type, TypeVar, List
from schemas import SQLRow, APIEndpoint

import asyncio
import aiosqlite
import httpx
from icecream import ic

DB = "wb.db"
API_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjIsImVudCI6MSwiZXhwIjoxNzc3NTkzOTkxLCJpZCI6IjAxOWEzNTAzLTJjMzctN2E0Ni1iMmE4LTkwNzQyY2I0Y2QwNyIsImlpZCI6MTI0NTM4NzAsIm9pZCI6MTU2OTMsInMiOjAsInNpZCI6ImZmYTA4MmZiLWUxZTktNTdhYi05ZWQyLWM2ZjE3ZDNhZWZkYSIsInQiOnRydWUsInVpZCI6MTI0NTM4NzB9.Mqq4xLDKhdZ_92ptEWiQsK7gepAX1coB39eHcqqBIYuZXpCjbnj4ozVSsR2ENXRGVKxTzlwmLz3x1VRla2Wxkg"

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
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://statistics-api-sandbox.wildberries.ru/ping", headers=HEADERS)
            print("---PING---")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            ic(e)

ModelType = TypeVar('ModelType', bound=APIEndpoint)
async def query_api(client: httpx.AsyncClient, ModelClass: Type[APIEndpoint], query_params: dict) -> List[ModelType]:
    """
    Делает один запрос к API

    :param params: Параметры для тела запроса к API
    :param ModelClass: Модель для валидации
    """
    try:
        assert ModelClass._method == "GET"
        response: httpx.Response = await client.request(
            url=ModelClass._url,
            method=ModelClass._method,
            headers=HEADERS,
            params=query_params
        )

        response.raise_for_status()
        data = response.json()
        if ModelClass._json_key:
            for key in ModelClass._json_key:
                data = data.get(key)
        return [ModelClass(**item) for item in data]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get("X-Ratelimit-Retry", 5))
            print(f"Rate limit hit. Retrying after {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            return await query_api(client, ModelClass, query_params)
        else:
            ic()
            ic(response.json())
    except Exception as e:
        ic()
        # ic(response.json())
        raise e

async def query_with_pagination(ModelClass: Type[APIEndpoint], query_params: dict = {}, pagination_params: dict = {}, save_to_db: bool = False) -> List[ModelType]:
    """
    Обёртка с пагинацией. TODO: save_to_db на лету

    :param query_params: параметры для api запроса
    :param pagination_params: параметры для пагинации
    """
    assert not save_to_db
    data = []
    async with httpx.AsyncClient() as client:
        pagination = ModelClass._pagination(**pagination_params)
        response = True
        while response != [] and pagination:
            response = await query_api(client, ModelClass, query_params = (pagination | query_params))
            if not response or len(response) == 0:
                break
            pagination = ModelClass._pagination(response[-1], **pagination_params)
            data.extend(response)
    return data

async def save_to_db(data: List[Type[SQLRow]]):
    """Save data to table"""
    # Автоматически получаем поля из модели
    fields = list(data[0].model_dump().keys())
    columns = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    values = [tuple(item.model_dump()[field] for field in fields) for item in data]

    async with aiosqlite.connect(DB) as db:
        await db.executemany(
            f"INSERT INTO {data[0]._table} ({columns}) VALUES ({placeholders})",
            values
        )
        await db.commit()

async def main():
    """Main function to run the data pipeline"""
    await ping()

    from schemas import WBGoodsInfo, raw_goods_to_single_product, WBSale
    import datetime
    goods = await query_with_pagination(
        WBGoodsInfo
        # WBSale, pagination_params={"dateFrom": (datetime.datetime.now().replace(tzinfo=None) - datetime.timedelta(days=365*3)).isoformat(), "dateTo":datetime.datetime.now().replace(tzinfo=None)}, 
    )
    data = []
    for good in goods:
        data.extend(raw_goods_to_single_product(good))
    if len(data) == 0:
        return
    ic(data[-1])
    await save_to_db("sales", data)

if __name__ == "__main__":
    asyncio.run(main())
