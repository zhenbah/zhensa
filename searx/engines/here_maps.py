# SPDX-License-Identifier: AGPL-3.0-or-later
"""HERE Maps"""

from urllib.parse import quote

about = {
    "website": 'https://wego.here.com/',
    "wikidata_id": 'Q571087',
    "official_api_documentation": 'https://developer.here.com/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['map']
paging = False

search_url = "https://wego.here.com/search/{query}"


def request(query, params):
    params['url'] = search_url.format(query=quote(query))
    return params


def response(resp):
    results = []

    # Return a basic result that links to HERE Maps search
    query = resp.search_params.get('query', '')
    if query:
        results.append({
            'template': 'map.html',
            'title': f"HERE Maps: {query}",
            'url': f"https://wego.here.com/search/{quote(query)}",
            'address': {
                'name': query,
            },
        })

    return results