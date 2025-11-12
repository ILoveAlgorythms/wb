Я пишу скрипт на питоне чтобы получать данные о продажах с маркетплейса по API. Я использую pydantic для валидации. У меня есть специальная модель

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, ClassVar

class APIEndpoint(BaseModel):
    _url: ClassVar[str]
    _method: ClassVar[str]

от которой я наследуюсь, чтобы хранить настройки для запроса. Твоя задача -  по заданному эндпоинту написать мне модель (и только модель, без кода), чтобы с помощью её провалидировать и перевести из json'а в python класс. Если есть циклы, сделай вложенные модели и назови соответсвтующе (см. пример). Никакие ошибки и информацию о самом запросе складывать не нужно

Пример того, что нужно сделать:

url: https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter
метод: get
ответ api:
{
  "data": {
    "listGoods": [
      {
        "nmID": 98486,
        "vendorCode": "07326060",
        "sizes": [
          {
            "sizeID": 3123515574,
            "price": 500,
            "discountedPrice": 350,
            "clubDiscountedPrice": 332.5,
            "techSizeName": "42"
          }
        ],
        "currencyIsoCode4217": "RUB",
        "discount": 30,
        "clubDiscount": 5,
        "editableSizePrice": true,
        "isBadTurnover": true
      }
    ]
  },
  "error": false,
  "errorText": ""
}

Pydantic модель (твой ответ):
class SizeInfo(BaseModel):
    sizeID: int
    price: int
    discountedPrice: int
    clubDiscountedPrice: float
    techSizeName: str

class WBGoodsInfo(APIEndpoint):
    nmID: int
    vendorCode: str
    sizes: List[SizeInfo]
    currencyIsoCode4217: str
    discount: int
    clubDiscount: int
    editableSizePrice: bool
    isBadTurnover: bool

    _url: ClassVar[str] = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
    _method: ClassVar[str] = "GET"
    model_config = ConfigDict(from_attributes=True)

Теперь твоя очередь. 
url:
метод: 
ответ api:
