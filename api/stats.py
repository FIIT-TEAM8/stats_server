import datetime
from flask import Blueprint
from flask.json import jsonify
from flask import request
from math import ceil

import api.api_settings as api_settings
from .elastic import Elastic


# deafult numbers of articles returned by elasticsearch when calculating stats
DEFAULT_STATS_SIZE = 300

# deafult numbers of articles returned by elasticsearch when retrieving articles
DEFAULT_ARTICLE_SIZE = 10

# /api/search/
stats_blueprint = Blueprint("search_routes", __name__, url_prefix="/api/")

elastic = Elastic()


# transform date to YYYY-MM-DD format
def transform_date(old_date):
    old_date = old_date[0:16]
    return datetime.datetime.strptime(old_date, '%a, %d %b %Y').strftime('%Y-%m-%d')


# check if number of articles to be returned is valid 
def check_size_validity(size):
    
    if size >= DEFAULT_STATS_SIZE:
        size = DEFAULT_STATS_SIZE

    elif size <= 0:
        size = DEFAULT_STATS_SIZE

    return size


# transforms string of filter parametes from request to list
def string_to_list(params_str):

    # check if filter is used
    if not params_str:
        return None
    # transform keywords string into list
    elif params_str[0] == '[' and params_str[len(params_str) - 1] == ']':
        params_str = params_str[1:-1]
        params_list = params_str.split(',')
        params_list = [item.lstrip() for item in params_list]
        return params_list
    else:
        return None
        

# get statistics from elastic response
def get_stats(articles_meta):

    articles_by_region = {}
    articles_by_crime = {}
    articles_by_language = {}
    articles_by_date = {}

    for article in articles_meta:
        
        # sorted by date
        articles_by_date[article['_id']] = transform_date(article['_source']['published'][0])

        # count articles by country
        region = article['_source']['region']
        if region not in articles_by_region:
            articles_by_region[region] = []
        articles_by_region[region].append(article['_id'])

        # count articles by language
        language = article['_source']['language']
        if language not in articles_by_language:
            articles_by_language[language] = []
        articles_by_language[language].append(article['_id'])

        # count articles by crime
        crimes = article['_source']['keywords']
        for crime in crimes:
            if crime not in articles_by_crime:
                articles_by_crime[crime] = []
            articles_by_crime[crime].append(article['_id'])

    # sort results
    articles_by_region = dict(sorted(articles_by_region.items(), key=lambda i: -len(i[1])))
    articles_by_language = dict(sorted(articles_by_language.items(), key=lambda i: -len(i[1])))
    articles_by_crime = dict(sorted(articles_by_crime.items(), key=lambda i: -len(i[1])))
    articles_by_date = {k: v for k, v in sorted(articles_by_date.items(), key=lambda item: item[1], reverse=True)}

    stats = {
        "articles_by_region": articles_by_region,
        "articles_by_language": articles_by_language,
        "articles_by_crime": articles_by_crime,
        "articles_by_date": articles_by_date,
    }
    return stats


# transform 'ids' request argument into list of ids
def transform_ids(ids):
    article_ids = string_to_list(ids)
    article_ids = [curr.replace('\"', '') for curr in article_ids]
    article_ids = [curr.replace('\'', '') for curr in article_ids]
    return article_ids


# main function for searching
@stats_blueprint.route("/search", methods=["GET"])
def search():
    
    query = request.args.get(api_settings.API_SEARCH_QUERY, default=None, type=str)
    search_from = request.args.get(api_settings.API_SEARCH_FROM, default="", type=str)
    search_to = request.args.get(api_settings.API_SEARCH_TO, default="", type=str)
    size = request.args.get(api_settings.API_RESULT_SIZE, default=DEFAULT_STATS_SIZE, type=int)
    categories = request.args.get(api_settings.API_KEYWORDS, default="", type=str)
    regions = request.args.get(api_settings.API_REGIONS, default="", type=str)

    if query is None:
        return "Invalid input, please provide 'q' parameter", 400

    if elastic.check_connection() is None:
        return "Can't connect to Elasticsearch", 503

    size = check_size_validity(size)
    cat_list = string_to_list(categories)
    regions_list = string_to_list(regions)

    elastic_response = elastic.search(query, cat_list, regions_list, search_from, search_to, size)
    total_results = elastic_response["hits"]["total"]["value"]
    articles_count = len(elastic_response['hits']['hits'])
    articles_meta = elastic_response['hits']['hits']
    stats = get_stats(articles_meta)

    response = {
        "query": query,
        "search_from": search_from,
        "search_to": search_to,
        "total_results": total_results,
        "articles_count": articles_count,
        "stats": stats
    }

    return jsonify(response)


# function for returning articles that were selected from graph
@stats_blueprint.route("/selected", methods=["GET"])
def get_selection_by_ids():

    ids = request.args.get(api_settings.API_IDS, default=None, type=str)
    page_num = request.args.get(api_settings.API_PAGE_NUM, default=1, type=int)
    size = request.args.get(api_settings.API_PAGE_SIZE, default=DEFAULT_ARTICLE_SIZE, type=int)

    if ids is None:
        return "Invalid input, please provide 'ids' parameter", 400
        
    if elastic.check_connection() is None:
        return "Can't connect to Elasticsearch", 503

    if page_num <= 0:
        page_num = 1

    size = DEFAULT_ARTICLE_SIZE
    article_ids = transform_ids(ids)
    response = elastic.search_by_ids(article_ids, page_num, size)
    total_results = response["hits"]["total"]["value"]
    total_pages = int(ceil(total_results/size))

    hits = response["hits"]["hits"]
    articles = []

    for hit in hits:
        article = hit["_source"]
        article["preview"] = "Article preview is currently not supported."
        article.pop("html")
        article["_id"] = hit["_id"]
        articles.append(article)

    per_page = len(articles)

    response = {
        "page_num": page_num,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_results": total_results,
        "results": articles
    }

    return jsonify(response)