# SPDX-License-Identifier: AGPL-3.0-or-later
"""Yandex Maps"""

from urllib.parse import quote

about = {
    "website": 'https://yandex.com/maps/',
    "wikidata_id": 'Q1755674',
    "official_api_documentation": 'https://yandex.com/dev/maps/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False

search_url = "https://yandex.com/maps/?text={query}"


def request(query, params):
    params['url'] = search_url.format(query=quote(query))
    return params


def response(resp):
    results = []

    # Return a basic result that links to Yandex Maps search
    query = resp.search_params.get('query', '')
    if query:
        results.append({
            'template': 'map.html',
            'title': f"Yandex Maps: {query}",
            'url': f"https://yandex.com/maps/?text={quote(query)}",
            'address': {
                'name': query,
            },
        })

    return results