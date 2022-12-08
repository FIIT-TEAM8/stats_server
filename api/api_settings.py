import os

# API parameters
# /search endpoint
API_SEARCH_QUERY = "q"
API_SEARCH_FROM = "from"
API_SEARCH_TO = "to"
API_RESULT_SIZE = "size"
API_KEYWORDS = "keywords"
API_REGIONS = "regions"

# articles endpoint
API_IDS = "ids"
API_PAGE_NUM = "page"
API_PAGE_SIZE = "size"

# environmental variables
ES_HOST = str(os.getenv('ES_HOST') or 'localhost')
ES_PORT = str(os.getenv('ES_PORT') or 9200)
ES_USER = str(os.getenv('ES_USER') or 'elastic')
ES_PASSWORD = str(os.getenv('ES_PASSWORD') or 'elastic123')
ELASTIC_INDEX_NAME = str(os.getenv('ELASTIC_INDEX_NAME') or 'articles_index')
ES_PROTOCOL="https"


ES_CONNECTION_STRING = "{protocol}://{username}:{password}@{host}:{port}/".format(
    protocol=ES_PROTOCOL,
    username=ES_USER,
    password=ES_PASSWORD,
    host=ES_HOST,
    port=ES_PORT
)

ES_URL = "{protocol}://{host}:{port}/{index}/".format(
    protocol=ES_PROTOCOL,
    host=ES_HOST,
    port=ES_PORT,
    index=ELASTIC_INDEX_NAME
)

ES_SEARCH_STRING = "{protocol}://{host}:{port}/{index}/_search".format(
    protocol=ES_PROTOCOL,
    host=ES_HOST,
    port=ES_PORT,
    index=ELASTIC_INDEX_NAME
)