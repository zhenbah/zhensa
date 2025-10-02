# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google Shopping
"""

import time
from urllib.parse import urlencode
from lxml import html

from searx.utils import extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.network import get
from searx.exceptions import SearxEngineCaptchaException
from searx.enginelib.traits import EngineTraits
from searx.engines.google import (
    get_google_info,
    time_range_dict,
)

about = {
    "website": 'https://shopping.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['shopping']
paging = True
max_page = 50
time_range_support = True
safesearch = True

# specific xpath variables
suggestion_xpath = '//div[contains(@class, "EIaa9b")]//a'


def request(query: str, params):
    """Google Shopping search request"""
    # Use Google main search with shopping tab (more reliable than shopping.google.com)
    base_url = 'https://www.google.com/search'

    query_params = {
        'q': query,
        'tbm': 'shop',  # Shopping tab
        'start': (params['pageno'] - 1) * 10,
    }

    # Add language parameter if available
    searxng_locale = params.get('searxng_locale', 'en-US')
    if searxng_locale != 'all':
        lang_code = searxng_locale.split('-')[0] if '-' in searxng_locale else searxng_locale
        query_params['hl'] = lang_code

    if params['time_range'] in time_range_dict:
        query_params['tbs'] = 'qdr:' + time_range_dict[params['time_range']]

    params['url'] = f"{base_url}?{urlencode(query_params)}"

    # Set comprehensive headers to mimic a real browser
    params['headers'].update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })

    # Set required cookies for Google
    params['cookies'] = {
        'CONSENT': 'YES+',
        'SOCS': 'CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmVuIAEaBgiA2NixBg',
    }

    return params


def response(resp):
    """Get response from google's shopping search request"""
    results = []

    # convert the text to dom
    dom = html.fromstring(resp.text)

    # parse results from Google Shopping (main search with tbm=shop)
    # Look for shopping result containers - try multiple selectors
    shopping_containers = []

    # Try different possible container selectors
    shopping_containers.extend(eval_xpath_list(dom, '//div[contains(@class, "sh-dgr__grid-result")]'))
    shopping_containers.extend(eval_xpath_list(dom, '//div[contains(@class, "sh-dlr__list-result")]'))
    shopping_containers.extend(eval_xpath_list(dom, '//div[@data-docid]'))
    shopping_containers.extend(eval_xpath_list(dom, '//div[contains(@class, "u30d4")]'))
    shopping_containers.extend(eval_xpath_list(dom, '//div[contains(@class, "g")]//div[contains(@class, "rc")]'))  # Fallback to general results

    for container in shopping_containers:

        try:
            # Find the product link
            link = eval_xpath_getindex(container, './/a[contains(@href, "/shopping/product/")]', 0, None) or \
                  eval_xpath_getindex(container, './/a[contains(@href, "/url?")]', 0, None)
            if link is None:
                continue

            url = link.get('href')
            if not url:
                continue

            # Handle Google redirect URLs
            if url.startswith('/url?'):
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(url)
                query_params = parse_qs(parsed.query)
                if 'url' in query_params:
                    url = query_params['url'][0]

            # Get product title
            title_elem = eval_xpath_getindex(container, './/h3[contains(@class, "tAxDx")]', 0, None) or \
                        eval_xpath_getindex(container, './/span[contains(@class, "translate-content")]', 0, None) or \
                        eval_xpath_getindex(container, './/a//span', 0, None) or \
                        eval_xpath_getindex(link, './/text()', 0, None)

            title = extract_text(title_elem) if title_elem is not None else 'Product'

            # Get product image
            img_elem = eval_xpath_getindex(container, './/img', 0, None)
            thumbnail = None
            if img_elem is not None:
                img_src = img_elem.get('src')
                if img_src and (img_src.startswith('http') or img_src.startswith('data:')):
                    thumbnail = img_src

            # Get price
            price_elem = eval_xpath_getindex(container, './/span[contains(@class, "a8Pemb")]', 0, None) or \
                        eval_xpath_getindex(container, './/span[contains(@class, "OFFNJ")]', 0, None) or \
                        eval_xpath_getindex(container, './/span[contains(@class, "price")]', 0, None)

            price = extract_text(price_elem) if price_elem is not None else ''

            # Get merchant/store info
            merchant_elem = eval_xpath_getindex(container, './/div[contains(@class, "aULzUe")]', 0, None) or \
                           eval_xpath_getindex(container, './/cite', 0, None)
            merchant = extract_text(merchant_elem) if merchant_elem is not None else ''

            # Get rating and review count
            rating_elem = eval_xpath_getindex(container, './/span[contains(@class, "Rsc")]', 0, None)
            rating = extract_text(rating_elem) if rating_elem is not None else ''

            review_elem = eval_xpath_getindex(container, './/span[contains(@class, "Rsc")]/following-sibling::span', 0, None)
            reviews = extract_text(review_elem) if review_elem is not None else ''

            # Build content with shopping-specific formatting
            content_parts = []
            if price:
                content_parts.append(f"Price: {price}")
            if merchant:
                content_parts.append(f"Seller: {merchant}")
            if rating and reviews:
                content_parts.append(f"Rating: {rating} ({reviews})")
            elif rating:
                content_parts.append(f"Rating: {rating}")

            content = ' | '.join(content_parts) if content_parts else ''

            if title and url and url.startswith('http'):
                result = {
                    'url': url,
                    'title': title,
                    'content': content,
                    'thumbnail': thumbnail,
                    'price': price,
                    'merchant': merchant,
                    'rating': rating,
                    'reviews': reviews,
                    'template': 'shopping.html'  # Custom template for shopping results
                }
                results.append(result)

        except Exception:
            continue

    # If no shopping results found, try to extract from general search results
    if not results:
        # Fallback: try to get general search results
        for result in eval_xpath_list(dom, '//div[contains(@class, "g")]//div[contains(@class, "rc")]'):
            try:
                link = eval_xpath_getindex(result, './/a', 0, None)
                if link is None:
                    continue

                url = link.get('href')
                title_elem = eval_xpath_getindex(result, './/h3', 0, None)
                title = extract_text(title_elem) if title_elem is not None else extract_text(link)

                content_elem = eval_xpath_getindex(result, './/span[contains(@class, "aCOpRe")]', 0, None)
                content = extract_text(content_elem) if content_elem is not None else ''

                if title and url and url.startswith('http'):
                    results.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'template': 'shopping.html'
                    })

                if len(results) >= 10:  # Limit fallback results
                    break
            except Exception:
                continue

    # Limit results to avoid too many
    results = results[:20]

    return results


# get supported languages from their site
def fetch_traits(engine_traits: EngineTraits, add_domains: bool = True):
    """Fetch languages from Google Shopping."""
    # Import here to avoid circular imports
    from searx.engines.google import fetch_traits as google_fetch_traits

    # Use the same traits as regular Google search
    google_fetch_traits(engine_traits, add_domains)