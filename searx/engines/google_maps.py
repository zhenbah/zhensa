# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Maps"""

from urllib.parse import quote
from lxml import html

from searx.utils import extract_text, eval_xpath

about = {
    "website": 'https://maps.google.com/',
    "wikidata_id": 'Q3269157',
    "official_api_documentation": 'https://developers.google.com/maps',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False

search_url = "https://www.google.com/maps/search/{query}"


def request(query, params):
    params['url'] = search_url.format(query=quote(query))
    return params


def response(resp):
    results = []

    # For now, return a basic result that links to Google Maps search
    # Web scraping Google Maps is challenging due to dynamic content and anti-scraping measures
    query = resp.search_params.get('query', '')
    if query:
        results.append({
            'template': 'map.html',
            'title': f"Google Maps: {query}",
            'url': f"https://www.google.com/maps/search/{quote(query)}",
            'address': {
                'name': query,
            },
        })

    return results