import unittest
from unittest.mock import MagicMock,patch
from fastapi import HTTPException
from datetime import datetime
import logging
import json

from ..lib.UrlDatabase import DataBaseFactory,ShortUrl
from ..util.UrlHandle import UrlHandle,UrlHandleStrategy,HashBasedShortUrl,CreateURLRequest
from ..config import Config

logging.getLogger().addHandler(logging.NullHandler())

def get_short_url(url_handler:UrlHandleStrategy,url_request:CreateURLRequest):
    response = url_handler.generate_short_url(url_request)
    content = response.body.decode("utf-8")
    content_dict = json.loads(content)
    return content_dict['short_url']

class TestUrlHandle(unittest.TestCase):
    def setUp(self):
        self.url_request:CreateURLRequest = {
            "original_url":"https://www.example.com/some/very/long/path"
        }
        self.db_url = ShortUrl(
                short_url = "a"*Config.SHORT_URL_LENGTH,
                origin_url = "https://www.abc.com/some/very/long/path",
                expiration_date = datetime(2025, 1, 1, 12, 0, 0)
            )

    def testHashStrategy(self):
        url_handler = UrlHandle(HashBasedShortUrl)
        url_request = self.url_request
        domain_name,short_url = get_short_url(url_handler,url_request).split("short-url/")
        self.assertEqual(len(short_url),Config.SHORT_URL_LENGTH)

        url_database = DataBaseFactory.get_database("short_url")
        retrieved_url = url_database.query(short_url)
        self.assertIsNotNone(retrieved_url, "Retrieved url should not be None")
        self.assertEqual(retrieved_url.origin_url, self.url_request['original_url'])

        #same origin url
        domain_name,short_url = get_short_url(url_handler,url_request).split("short-url/")
        self.assertEqual(short_url,retrieved_url.short_url)
        url_database.delete(short_url)

    
    @patch.object(DataBaseFactory, 'get_database')
    def testHashStrategy_conflict_generate_sucess(self,mock_get_database):
        url_database = DataBaseFactory.get_database("short_url")

        # generate sucess
        mock_url_db = MagicMock()
        mock_url_db.query.side_effect = [self.db_url, None, None]
        mock_get_database.return_value = mock_url_db
        url_handler = UrlHandle(HashBasedShortUrl)
        url_request = self.url_request
        domain_name,short_url = get_short_url(url_handler,url_request).split("short-url/")
        self.assertIsInstance(short_url,str)
        self.assertEqual(len(short_url),Config.SHORT_URL_LENGTH)
        url_database.delete(short_url)

    @patch.object(DataBaseFactory, 'get_database')
    def testHashStrategy_conflict_generate_fail(self,mock_get_database):

        # generatr fail
        mock_url_db = MagicMock()
        mock_url_db.query.side_effect = [self.db_url] * 6
        mock_get_database.return_value = mock_url_db
        url_handler = UrlHandle(HashBasedShortUrl)
        url_request = self.url_request
        with self.assertRaises(HTTPException):
            short_url = get_short_url(url_handler,url_request)

    def testHashStrategy_url_valid(self):
        url_handler = UrlHandle(HashBasedShortUrl)
        long_request:CreateURLRequest = {
            "original_url":"https://" + "a" * 2049
        }
        response = url_handler.generate_short_url(long_request)
        content = response.body.decode("utf-8")
        content_dict = json.loads(content)
        self.assertEqual(content_dict['reason'],'URL too long')

        wrong_request:CreateURLRequest = {
            "original_url":"a" * 10
        }
        response = url_handler.generate_short_url(wrong_request)
        content = response.body.decode("utf-8")
        content_dict = json.loads(content)
        self.assertEqual(content_dict['reason'],'Invalid URL')
    
    def testHashStrategy_get_original_url(self):
        url_handler = UrlHandle(HashBasedShortUrl)
        url_request = self.url_request
        domain_name,short_url = get_short_url(url_handler,url_request).split("short-url/")
        response = url_handler.redirect_url(short_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["location"], self.url_request["original_url"])

        with self.assertRaises(HTTPException):
            short_url = url_handler.redirect_url("b"*Config.SHORT_URL_LENGTH)

if __name__ == '__main__':
    unittest.main()