from datetime import date
from decimal import Decimal
from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger


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
    isin: str
    rate: float
    cut_off_price: float
    yield_to_maturity: float
    offered: int = Field(sa_column=BigInteger())
    tendered: int = Field(sa_column=BigInteger())
    competitive_offer: int = Field(sa_column=BigInteger())
    non_competitive_offer: int = Field(sa_column=BigInteger())
    accepted_bids: int = Field(sa_column=BigInteger())
    accepted_competitive_bids: int = Field(sa_column=BigInteger())
    accepted_non_competitive_bids: int = Field(sa_column=BigInteger())
    bid_cover_ratio: float
