from abc import ABC,abstractmethod
import hashlib
import base64
import string
import secrets
from fastapi import HTTPException
from fastapi.responses import JSONResponse,RedirectResponse
import logging
from datetime import datetime,timedelta
from urllib.parse import urlparse
from functools import wraps
from typing import TypedDict

from ..lib.UrlDatabase import DataBaseFactory,ShortUrlData
from ..config import Config

class CreateURLRequest(TypedDict):
    original_url:str

class CreateURLResponse(TypedDict):
    short_url:str
    expiration_date:float
    sucess:bool
    reason:str

class UrlHandleStrategy(ABC):
    @abstractmethod
    def generate_short_url(self,url:str) -> str:
        pass

def random_string(length=Config.SHORT_URL_LENGTH):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

class HashBasedShortUrl(UrlHandleStrategy):
    def __init__(self):
        self.length = Config.SHORT_URL_LENGTH
        self.url_db = DataBaseFactory.get_database("short_url")
    def generate_short_url(self, url:str) -> dict:
        hashed_url = hashlib.sha256(url.encode()).digest()
        base64_string = base64.urlsafe_b64encode(hashed_url).decode()
        short_url = base64_string[:self.length]
        retry_time = Config.GENERATE_URL_RETRY

        retrieved_url = self.url_db.query(short_url)
        
        if retrieved_url is not None and retrieved_url.origin_url == url:
            return {
                "short_url":short_url,
                "origin_url" : retrieved_url.origin_url,
                "expiration_date":retrieved_url.expiration_date.timestamp()
            }

        if retrieved_url is not None and retry_time:
            short_url  = random_string()
            retrieved_url = self.url_db.query(short_url)
            retry_time -= 1

        if retrieved_url is not None:
            logging.error(f'Url random generate duplicate over 5 times.')
            raise HTTPException(
                status_code=500,
            )
        short_url_data:ShortUrlData = {
            "short_url":short_url,
            "origin_url" : url,
            "expiration_date":datetime.now() + timedelta(days = Config.STORE_DAYS)
        }
        self.url_db.insert(short_url_data)
        return {
            "short_url":short_url,
            "origin_url" : url,
            "expiration_date":short_url_data["expiration_date"].timestamp()
        }
    def get_original_url(self,short_url:str):
        retrieved_url = self.url_db.query(short_url)
        if not retrieved_url:
            raise HTTPException(status_code=404, detail="Short url not found")
        return retrieved_url.origin_url

class UrlHandle():
    def __init__(self,url_handle_strategy:UrlHandleStrategy):
        self.url_handler = url_handle_strategy()
    def generate_short_url(self,create_url_request:CreateURLRequest) -> CreateURLResponse: 
        if len(create_url_request['original_url']) > 2048:
            return JSONResponse(
                status_code=400,
                content={
                    "short_url": None,
                    "expiration_date":None,
                    "sucess": False,
                    "reason": "URL too long",
                }
            )
        
        parsed = urlparse(create_url_request['original_url'])
        if not all([parsed.scheme, parsed.netloc]):
            return JSONResponse(
                status_code=400,
                content={
                    "short_url": None,
                    "expiration_date":None,
                    "sucess": False,
                    "reason": "Invalid URL",
                }
            )

        short_url_data = self.url_handler.generate_short_url(create_url_request['original_url'])
        return JSONResponse(
                status_code=200,
                content={
                    "short_url": f"{Config.DOMAIN_NAME}short-url/{short_url_data['short_url']}",
                    "expiration_date":short_url_data['expiration_date'],
                    "sucess": True,
                    "reason": None,
                }
            )
    def redirect_url(self,short_url:str):
        original_url = self.url_handler.get_original_url(short_url)
        return RedirectResponse(url=original_url, status_code=302)
        