from flask import jsonify
import requests
import json
import api.api_settings as api_settings

# first and last avaliable years when using date filter
FIRST_YEAR = 2000
LAST_YEAR = 2100


# handle elasticsearch through requests library
class Elastic:
    def __init__(self):
        with open('static/en_keyword_categories.json', encoding='utf8') as file:
            self.en_keyword_categories = json.load(file)

    
    # test request to check connection
    def check_connection(self):
        try:
            response = requests.get("{protocol}://{host}:{port}/".format(
                    protocol=api_settings.ES_PROTOCOL,
                    host=api_settings.ES_HOST,
                    port=api_settings.ES_PORT
                ),
                verify=False, 
                auth=(api_settings.ES_USER, api_settings.ES_PASSWORD))
            
            if response.status_code == 200:
                return True
            return None

        except Exception as e:
            return None


    def load_keywords(self, categories):
        keywords = []

        for cat in categories:
            # TODO: check if category exists and if not, inform user
            cat_keywords = self.en_keyword_categories[cat]
            keywords.extend(cat_keywords)

        return keywords


    # get ids from elasticsearch results
    def get_ids(self, results):
        ids = []

        for res in results["hits"]["hits"]:
            ids.append(res["_id"])

        return ids
    

    # builds elasticsearch query with or without filters
    def build_query(self, query, categories, regions, search_from, search_to, size):
        self.body = {
            "_source": ["keywords", "region", "language", "published", "link"],
            "size": str(size),
            "query": {
                "bool": {
                    "must": [{
                        "multi_match": {
                            "query": query,
                            "type": "phrase", 
                            "fields": [
                                "html"
                            ]
                        }
                    }]
                }
            }
        }

        # add crime keywords filter
        if categories:
            keywords = self.load_keywords(categories)
            keywords_filter = {
                "terms": {
                    "keywords.keyword": keywords
                }
            }
            self.body["query"]["bool"]["must"].append(keywords_filter)
        
        # add regions filter
        if regions:
            regions_filter = {
                "terms": {
                    "region": regions
                }
            }
            self.body["query"]["bool"]["must"].append(regions_filter)
        
        # add filtering by date
        if search_from or search_to:
            date_filter = { 
                "range": {
                    "published": {
                    }
                }
            }
            if search_from:
                year_from = search_from[:4]
                date_filter["range"]["published"]["gte"] = year_from
                if not search_to:
                    date_filter["range"]["published"]["lte"] = LAST_YEAR

            if search_to:
                year_to = search_to[:4]
                date_filter["range"]["published"]["lte"] = year_to
                if not search_from:
                    date_filter["range"]["published"]["gte"] = FIRST_YEAR

            self.body["query"]["bool"]["must"].append(date_filter)


    # build query then search
    def search(self, query, categories, regions, search_from, search_to, size):
        self.build_query(query, categories, regions, search_from, search_to, size)
        headers = {}
        response = requests.get(api_settings.ES_SEARCH_STRING, 
            headers=headers, 
            json=self.body, 
            verify=False, 
            auth=(api_settings.ES_USER, api_settings.ES_PASSWORD))
        return response.json()


    # search articles by ids
    def search_by_ids(self, ids, page_num, size):
    
        query = {
            "from": str(page_num * size - size), 
            "size": str(size),
            "query": {
                "terms": {
                    "_id": ids 
                }
            }
        }

        response = requests.get(api_settings.ES_SEARCH_STRING, 
            headers={},
            json=query,
            verify=False,
            auth=(api_settings.ES_USER, api_settings.ES_PASSWORD))

        results = response.json()
        return results