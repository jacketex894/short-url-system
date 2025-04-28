import yaml

with open('short_url_service/config.yaml','r') as file:
    config = yaml.safe_load(file)

class Config:
    URL_DATABASE_URL = f"mysql+pymysql://{config['MYSQL_DB']['MYSQL_USER']}:{config['MYSQL_DB']['MYSQL_PASSWORD']}@{config['MYSQL_DB']['HOST']}:{config['MYSQL_DB']['DATABASE_PORT']}/{config['MYSQL_DB']['URL_DB']}"
    SHORT_URL_LENGTH =  config['SHORT_URL']['LENGTH']
    GENERATE_URL_RETRY = config['SHORT_URL']['RETRY_TIME']
    STORE_DAYS = config['SHORT_URL']['STORE_DAYS']
    DOMAIN_NAME = config['DOMAIN_NAME']