# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing Maps"""

from urllib.parse import quote

about = {
    "website": 'https://www.bing.com/maps/',
    "wikidata_id": 'Q181565',
    "official_api_documentation": 'https://docs.microsoft.com/en-us/bingmaps/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False

search_url = "https://www.bing.com/maps?q={query}"


def request(query, params):
    params['url'] = search_url.format(query=quote(query))
    return params


def response(resp):
    results = []

    # Return a basic result that links to Bing Maps search
    query = resp.search_params.get('query', '')
    if query:
        results.append({
            'template': 'map.html',
            'title': f"Bing Maps: {query}",
            'url': f"https://www.bing.com/maps?q={quote(query)}",
            'address': {
                'name': query,
            },
        })

    return results