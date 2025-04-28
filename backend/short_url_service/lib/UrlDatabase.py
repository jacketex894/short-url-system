from abc import ABC,abstractmethod
import logging
from sqlalchemy import create_engine,Column,String,TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import TypedDict
from fastapi import HTTPException

from ..config import Config

class DataBase(ABC):
    @abstractmethod
    def insert():
        pass
    def query():
        pass
    def update():
        pass
    def delete():
        pass


class ShortUrlData(TypedDict):
    short_url:str
    origin_url:str
    expiration_date:datetime

class ShortUrl(declarative_base()):
    __tablename__ = 'short_url'

    short_url = Column(String(Config.SHORT_URL_LENGTH), primary_key=True)
    origin_url = Column(String(2048), nullable=False)
    expiration_date = Column(TIMESTAMP)

class UrlDB(DataBase):
    def __init__(self):
        engine = create_engine(Config.URL_DATABASE_URL)
        self.session = sessionmaker(bind=engine)

    def insert(self,short_url_data:ShortUrlData):
        session = self.session()
        try:
            new_short_url = ShortUrl(
                short_url = short_url_data['short_url'],
                origin_url = short_url_data['origin_url'],
                expiration_date = short_url_data['expiration_date']
            )
            session.add(new_short_url)
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f'Short url database insert error occurred: {e}')
            raise HTTPException(
                status_code=500,
            )
        finally:
            session.close()
    def query(self,short_url:str) -> ShortUrl:
        session = self.session()
        try:
            retrieved_url = session.query(ShortUrl).filter(ShortUrl.short_url == short_url).first()
        except Exception as e:
            logging.error(f'Short url database query error occurred: {e}')
            raise HTTPException(
                status_code=500,
            )
        finally:
            session.close()
        return retrieved_url
    def update(self,short_url:str,expiration_date:datetime) -> None:
        session = self.session()
        try:
            retrieved_url = session.query(ShortUrl).filter(ShortUrl.short_url == short_url).first()
            if retrieved_url:
                retrieved_url.expiration_date = expiration_date
                session.commit()
            else:
                logging.error(f'Update not exist url')
                raise HTTPException(
                    status_code=500,
                )
        except Exception as e:
            session.rollback()
            logging.error(f'Short url database update error occurred: {e}')
            raise HTTPException(
                status_code=500,
            )
        finally:
            session.close()
    def delete(self,short_url:str) -> None:
        session = self.session()
        try:
            retrieved_url = session.query(ShortUrl).filter(ShortUrl.short_url == short_url).first()
            if retrieved_url:
                session.delete(retrieved_url)
                session.commit()
            else:
                logging.error(f'Delete not exist url')
                raise HTTPException(
                    status_code=500,
                )
        except Exception as e:
            session.rollback()
            logging.error(f'Short url database delete error occurred: {e}')
            raise HTTPException(
                status_code=500,
            )
        finally:
            session.close()
class DataBaseFactory():
    @staticmethod
    def get_database(database:str) -> DataBase|None:
        match database:
            case "short_url":
                return UrlDB()
            case _:
                logging.error(f"Database {database} not exist.")
                return None
        