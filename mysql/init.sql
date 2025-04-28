CREATE DATABASE url_db;
USE url_db;
CREATE TABLE short_url(
    short_url VARCHAR(6) PRIMARY KEY,
    origin_url VARCHAR(2048) NOT NULL,
    expiration_date TIMESTAMP NOT NULL
);