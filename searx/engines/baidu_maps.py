# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu Maps"""

from urllib.parse import quote
from lxml import html

from searx.utils import extract_text, eval_xpath

about = {
    "website": 'https://map.baidu.com/',
    "wikidata_id": 'Q327143',
    "official_api_documentation": 'https://lbsyun.baidu.com/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False

search_url = "https://map.baidu.com/search/{query}"


def request(query, params):
    params['url'] = search_url.format(query=quote(query))
    return params


def response(resp):
    results = []

    # For now, return a basic result that links to Baidu Maps search
    # Web scraping Baidu Maps is challenging due to dynamic content
    query = resp.search_params.get('query', '')
    if query:
        results.append({
            'template': 'map.html',
            'title': f"Baidu Maps: {query}",
            'url': f"https://map.baidu.com/search/{quote(query)}",
            'address': {
                'name': query,
            },
        })

    return results