from datetime import date
from decimal import Decimal
from sqlmodel import Field, SQLModel


class AuctionCalendar(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    auction_date: date
    settlement_date: date
    maturity_date: date
    instrument: str = Field(index=True)
    currency: str = Field(default="UGX", index=True)
    tenure: int
    isin: str
    rate: Decimal | None = Field(default=None)


class AuctionResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    auction_date: date
    settlement_date: date
    maturity_date: date
    instrument: str = Field(index=True)
    currency: str = Field(default="UGX", index=True)
    tenure: int
    ISIN: str
    rate: Decimal | None = Field(default=None)
