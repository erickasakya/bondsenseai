import pandas as pd
from sqlmodel import Session, select
from db.model import AuctionCalendar, AuctionResult
from db.database import get_session
from fastapi import Depends
from typing import Annotated
from datetime import date

SessionDep = Annotated[Session, Depends(get_session)]


def parse_excel(file_path: str) -> pd.DataFrame:
    df = pd.read_excel(file_path)

    df["auction_date"] = pd.to_datetime(df["auction_date"], dayfirst=True)
    df["settlement_date"] = pd.to_datetime(df["settlement_date"], dayfirst=True)
    df["maturity_date"] = pd.to_datetime(df["maturity_date"], errors="coerce")
    df["instrument"] = df["instrument"].str.strip()
    df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce")
    df["isin"] = df["isin"].str.strip()
    df["rate"] = df["rate"].str.replace("%", "").astype(float)

    return df


def insert_calendars(session: Session, calendars_df):
    for _, row in calendars_df.iterrows():
        calendar = AuctionCalendar(
            auction_date=row["auction_date"].date(),
            settlement_date=row["settlement_date"].date(),
            maturity_date=row["maturity_date"].date(),
            instrument=row["instrument"],
            tenure=int(row["tenure"]),
            isin=row["isin"].strip(),
            rate=row["rate"],
        )
        session.add(calendar)
    session.commit()


def insert_auction_result(session: Session, auction_result_df):
    for _, row in auction_result_df.iterrows():
        result = AuctionResult(
            auction_date=row["auction_date"].date(),
            settlement_date=row["settlement_date"].date(),
            maturity_date=row["maturity_date"].date(),
            instrument=row["instrument"],
            tenure=int(row["tenure"]),
            isin=row["isin"].strip(),
            rate=row["rate"],
            cut_off_price=row["cut_off_price"],
            yield_to_maturity=row["yield_to_maturity"],
            offered=row["offered"],
            tendered=row["tendered"],
            competitive_offer=row["competitive_offer"],
            non_competitive_offer=row["non_competitive_offer"],
            accepted_bids=row["accepted_bids"],
            accepted_competitive_bids=row["accepted_competitive_bids"],
            accepted_non_competitive_bids=row["accepted_non_competitive_bids"],
            bid_cover_ratio=row["bid_cover_ratio"],
        )
        session.add(result)
    session.commit()


def get_calendar(instrument: str, tenure: int, session: Session):
    """Get the calendar for a given instrument."""
    sql_statement = select(AuctionCalendar).where(
        AuctionCalendar.instrument == instrument, AuctionCalendar.tenure == tenure
    )
    result = session.exec(sql_statement).all()
    return result


today = date.today()


def next_auction(instrument: str, tenure: int, session: Session):
    """Get the next auction date for a given instrument."""
    sql_statement = (
        select(AuctionCalendar)
        .where(
            AuctionCalendar.instrument == instrument,
            AuctionCalendar.tenure == tenure,
            AuctionCalendar.auction_date > today,
        )
        .order_by(AuctionCalendar.auction_date.asc())
    )
    result = session.exec(sql_statement).first()
    return result


def last_auction(instrument: str, tenure: int, session: Session):
    """Get the last auction date for a given instrument."""
    sql_statement = (
        select(AuctionCalendar)
        .where(
            AuctionCalendar.instrument == instrument,
            AuctionCalendar.tenure == tenure,
            AuctionCalendar.auction_date < today,
        )
        .order_by(AuctionCalendar.auction_date.desc())
    )
    result = session.exec(sql_statement).first()
    return result


def last_auction_offer(instrument: str, tenure: int, session: Session):
    """Get the last auction offer details for a given instrument."""
    sql_statement = (
        select(AuctionResult)
        .where(
            AuctionResult.instrument == instrument,
            AuctionResult.tenure == tenure,
            AuctionResult.auction_date < today,
        )
        .order_by(AuctionResult.auction_date.desc())
    )
    result = session.exec(sql_statement).first()
    return result


def count_auctions(instrument: str, tenure: int, session: Session):
    """Count the total number of auctions for a given instrument."""
    sql_statement = select(AuctionCalendar).where(
        AuctionCalendar.instrument == instrument,
        AuctionCalendar.tenure == tenure,
    )
    result = session.exec(sql_statement).all()
    return len(result)
