import unittest
from datetime import datetime,timedelta
from fastapi import HTTPException
import logging

from ..lib.UrlDatabase import DataBaseFactory,ShortUrlData
from ..config import Config

logging.getLogger().addHandler(logging.NullHandler())
class TestUrlDataBase(unittest.TestCase):
    def setUp(self):
        self.short_url_data:ShortUrlData = {
            "short_url":"a" * Config.SHORT_URL_LENGTH,
            "origin_url" : "https://www.example.com/some/very/long/path",
            "expiration_date" : datetime(2025, 1, 1, 12, 0, 0) + timedelta(days = 30)
        }
        self.update_expiration_date = datetime(2025, 1, 1, 13, 0, 0)
        self.not_exist_url = "b" * Config.SHORT_URL_LENGTH
    def testCRUD(self):
        url_database = DataBaseFactory.get_database("short_url")

        #insert 
        url_database.insert(self.short_url_data)
        #duplicate check
        with self.assertRaises(HTTPException):
            url_database.insert(self.short_url_data)

        #query
        retrieved_url = url_database.query(self.short_url_data["short_url"])
        self.assertIsNotNone(retrieved_url, "Retrieved url should not be None")
        self.assertEqual(retrieved_url.origin_url, self.short_url_data["origin_url"])
        self.assertEqual(retrieved_url.expiration_date, self.short_url_data["expiration_date"])

        #update
        #update not exist url
        with self.assertRaises(HTTPException):
            url_database.update(self.not_exist_url,self.update_expiration_date)

        url_database.update(self.short_url_data["short_url"],self.update_expiration_date)
        retrieved_url = url_database.query(self.short_url_data["short_url"])
        self.assertEqual(retrieved_url.origin_url, self.short_url_data["origin_url"])
        self.assertEqual(retrieved_url.expiration_date, self.update_expiration_date)

        #delete
        with self.assertRaises(HTTPException):
            url_database.delete(self.not_exist_url)
        url_database.delete(self.short_url_data["short_url"])
        deleted_url = url_database.query(self.short_url_data["short_url"])
        self.assertIsNone(deleted_url, "Deleted url should be None")
        



if __name__ == '__main__':
    unittest.main()