# поля совпадают с полями API
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, ClassVar, Optional, Self

# TODO: отдельные модели для ответов API и для бд, простая конвертация

# 'internal_field_name' is the name you'll use in your Python code
# 'external_key_from_dict' is the key expected in the input dictionary
# internal_field_name: str = Field(alias='external_key_from_dict')
# another_field: int = Field(alias='different_name_in_dict')
# class DBSale(BaseModel):
#     name: str # HARPER HB-416
#     article: str # beige
#     brand: str
#     barcode: str
# Наименование	Артикул	Бренд	Баркод	Штрихкод	Артикул	Товарная группа	ID склада	Дата записи	В пути до клиента	В пути от клиента	Доступно к заказу	Всего
# HARPER HB-416 beige	HB-416 beige	HARPER	4 670 140 060 095	4 670 140 060 118	H00003535	Наушники	ID_Электросталь	06.10.2025	331	41	7 285	7657
# class DBStock(BaseModel):
#     name: str # HARPER HB-416 beige
#     article: str # HB-416 beige / H00003535 ?
#     brand: str # HARPER
#     barcode: str # 4670140060095 / 4670140060118 ?

class APIEndpoint(BaseModel):
    _url: ClassVar[str]
    _method: ClassVar[str]
    _json_key: ClassVar[Optional[List[str]]]

    @staticmethod
    def _pagination(response: Optional[dict] = None, **kwargs) -> Optional[dict]:
        """
        Принимает response от прошлого запроса (и дополительне параметры), возвращает параметры пагинации для нового запроса или None, если это последний

        Usage:
            ```python
            pagination = model_class._pagination(**pagination_params)
            while response != [] and pagination:
                response = await query_api(..., params = pagination | orig_params)
                pagination = model_class._pagination(response[-1], **pagination_params)
            ```
        """
        if response is None:
            return {"limit": 1000}
        return {"limit": response["limit"], "offset": response["limit"]+response["offset"]}

class SQLRow(BaseModel):
    """
    указывает, что класс сереализуется сразу в ровно одну запись в бд

    некоторые api эндпоинты возвращают объекты со списком внутри, в таком случае нужно конвертировать их к `SQLRow` классу
    """
    _table: ClassVar[str]

class WBSale(APIEndpoint, SQLRow):
    nmId: int # артикул вб
    lastChangeDate: datetime # Для одного ответа на запрос с flag=0 или без flag в системе установлено условное ограничение 80000 строк. Поэтому, чтобы получить все продажи и возвраты, может потребоваться более, чем один запрос. Во втором и далее запросе в параметре dateFrom используйте полное значение поля lastChangeDate из последней строки ответа на предыдущий запрос.
    # данные продажи
    date: datetime
    finishedPrice: float # Фактическая цена с учетом всех скидок (к взиманию с покупателя)
    forPay: float # К перечислению продавцу
    totalPrice: float # Цена без скидок
    # данные товара
    brand: str
    category: str
    barcode: str
    # ненужные поля
    countryName: str = Field(exclude=True)
    discountPercent: int = Field(exclude=True)
    gNumber: str = Field(exclude=True)
    incomeID: int = Field(exclude=True)
    isRealization: bool = Field(exclude=True)
    isSupply: bool = Field(exclude=True)
    oblastOkrugName: str = Field(exclude=True)
    priceWithDisc: float = Field(exclude=True)
    regionName: str = Field(exclude=True)
    saleID: str = Field(exclude=True)
    spp: float = Field(exclude=True)
    srid: str = Field(exclude=True)
    sticker: str = Field(exclude=True)
    subject: str = Field(exclude=True)
    supplierArticle: str = Field(exclude=True)
    techSize: str = Field(exclude=True)
    warehouseName: str = Field(exclude=True)
    warehouseType: str = Field(exclude=True)


    _url: ClassVar[str] = "https://statistics-api-sandbox.wildberries.ru/api/v1/supplier/sales"
    _method: ClassVar[str] = "GET"
    _json_key: ClassVar[Optional[List[str]]] = None
    @staticmethod
    def _pagination(response: Optional[Self] = None, **kwargs) -> Optional[dict]:
        if response is None:
            return {"dateFrom": kwargs.get("dateFrom")}
        if response.lastChangeDate.replace(tzinfo=None) > kwargs.get("dateTo"):
            return None
        return {"dateFrom": response.lastChangeDate.isoformat()}

    _table: ClassVar[str] = "sales"
    model_config = ConfigDict(from_attributes=True)

class WBStock(APIEndpoint, SQLRow):
    nmId: int
    lastChangeDate: datetime

    quantity: int

    brand: str
    category: str
    barcode: str

    warehouseName: str = Field(exclude=True)
    supplierArticle: str = Field(exclude=True)
    inWayToClient: int = Field(exclude=True)
    inWayFromClient: int = Field(exclude=True)
    quantityFull: int = Field(exclude=True)
    subject: str = Field(exclude=True)
    Discount: int = Field(exclude=True)
    Price: int = Field(exclude=True)
    SCCode: str = Field(exclude=True)
    daysOnSite: int = Field(exclude=True)
    isRealization: bool = Field(exclude=True)
    isSupply: bool = Field(exclude=True)
    techSize: str = Field(exclude=True)

    _url: ClassVar[str] = "https://statistics-api-sandbox.wildberries.ru/api/v1/supplier/stocks"
    _method: ClassVar[str] = "GET"
    _json_key: ClassVar[Optional[List[str]]] = None
    @staticmethod
    def _pagination(response: Optional[Self] = None, **kwargs) -> Optional[dict]:
        if response is None:
            return {"dateFrom": kwargs.get("dateFrom")}
        if response.lastChangeDate.replace(tzinfo=None) > kwargs.get("dateTo"):
            return None
        return {"dateFrom": response.lastChangeDate.isoformat()}

    _table: ClassVar[str] = "stocks"

    model_config = ConfigDict(from_attributes=True)


class _SizeInfo(BaseModel):
    sizeID: int
    price: int
    discountedPrice: int
    clubDiscountedPrice: float
    techSizeName: str

class WBGoodsInfo(APIEndpoint):
    nmID: int
    vendorCode: str = Field(exclude=True)
    sizes: List[_SizeInfo] = Field(exclude=True)
    currencyIsoCode4217: str
    discount: int
    clubDiscount: float
    editableSizePrice: bool = Field(exclude=True)
    isBadTurnover: bool

    _url: ClassVar[str] = "https://discounts-prices-api-sandbox.wildberries.ru/api/v2/list/goods/filter"
    _method: ClassVar[str] = "GET"
    _json_key: ClassVar[Optional[List[str]]] = ["data", "listGoods"]
    model_config = ConfigDict(from_attributes=True)

class WBProduct(SQLRow):
    """
    Информация от WBGoodsInfo по размерам.

    Получается не напрямую от API, а через `raw_goods_to_single_product`
    """
    nmID: int
    currencyIsoCode4217: str
    discount: int
    clubDiscount: float
    isBadTurnover: bool
    request_received_at: datetime = Field(default_factory=datetime.now)

    # Size info
    sizeID: int
    price: int
    discountedPrice: int
    clubDiscountedPrice: float
    techSizeName: str

    _table: ClassVar[str] = "items"
    model_config = ConfigDict(from_attributes=True, extra='ignore')

def raw_goods_to_single_product(raw_goods: WBGoodsInfo) -> List[WBProduct]:
    return [WBProduct(**raw_goods.model_dump(), **size.model_dump()) for size in raw_goods.sizes]