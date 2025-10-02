# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bing Shopping
"""

import base64
import re
import time
from urllib.parse import parse_qs, urlencode, urlparse
from lxml import html

from searx.utils import eval_xpath, extract_text, eval_xpath_list, eval_xpath_getindex
from searx.exceptions import SearxEngineAPIException

about = {
    "website": 'https://www.bing.com',
    "wikidata_id": 'Q182496',
    "official_api_documentation": 'https://www.microsoft.com/en-us/bing/apis/bing-web-search-api',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

# engine dependent config
categories = ['shopping']
paging = True
max_page = 200
"""200 pages maximum"""

time_range_support = True
safesearch = True

base_url = 'https://www.bing.com/shop'


def _page_offset(pageno):
    return (int(pageno) - 1) * 10 + 1


def request(query, params):
    """Assemble a Bing Shopping request."""

    page = params.get('pageno', 1)
    query_params = {
        'q': query,
    }

    if page > 1:
        query_params['first'] = _page_offset(page)

    params['url'] = f'{base_url}?{urlencode(query_params)}'

    if params.get('time_range'):
        unix_day = int(time.time() / 86400)
        time_ranges = {'day': '1', 'week': '2', 'month': '3', 'year': f'5_{unix_day-365}_{unix_day}'}
        params['url'] += f'&filters=ex1:"ez{time_ranges[params["time_range"]]}"'

    return params


def response(resp):
    results = []
    result_len = 0

    dom = html.fromstring(resp.text)

    # parse results - try multiple selectors for Bing Shopping
    shopping_results = []

    # Try different possible result selectors
    shopping_results.extend(eval_xpath_list(dom, '//div[contains(@class, "iusc")]//a'))
    shopping_results.extend(eval_xpath_list(dom, '//li[contains(@class, "b_algo")]//h2//a'))
    shopping_results.extend(eval_xpath_list(dom, '//a[contains(@href, "/shop/")]'))
    shopping_results.extend(eval_xpath_list(dom, '//a[contains(@href, "bing.com/shop")]'))

    for result in shopping_results:
        if result is None:
            continue

        url = result.get('href') or result.attrib.get('href')
        if not url:
            continue

        title = extract_text(result)

        # Try to get content from various possible locations
        content_elem = None
        content_elem = content_elem or eval_xpath(result, '../div[@class="iusc"]//div[@class="iusc"]')
        content_elem = content_elem or eval_xpath(result, '../../div[contains(@class, "b_caption")]//p')
        content_elem = content_elem or eval_xpath(result, '../following-sibling::div//p')

        content = extract_text(content_elem[0]) if content_elem else ''

        # get the real URL
        if url.startswith('https://www.bing.com/ck/a?'):
            # get the first value of u parameter
            url_query = urlparse(url).query
            parsed_url_query = parse_qs(url_query)
            param_u = parsed_url_query["u"][0]
            # remove "a1" in front
            encoded_url = param_u[2:]
            # add padding
            encoded_url = encoded_url + '=' * (-len(encoded_url) % 4)
            # decode base64 encoded URL
            url = base64.urlsafe_b64decode(encoded_url).decode()

        # append result
        results.append({'url': url, 'title': title, 'content': content})

    # If no shopping results found, try general Bing results as fallback
    if not results:
        for result in eval_xpath_list(dom, '//ol[@id="b_results"]/li[contains(@class, "b_algo")]'):
            link = eval_xpath_getindex(result, './/h2/a', 0, None)
            if link is None:
                continue
            url = link.attrib.get('href')
            title = extract_text(link)

            content = eval_xpath(result, './/p')
            for p in content:
                # Make sure that the element is free of certain spans
                for e in p.xpath('.//span[@class="algoSlug_icon"]'):
                    e.getparent().remove(e)
            content = extract_text(content)

            # get the real URL
            if url.startswith('https://www.bing.com/ck/a?'):
                url_query = urlparse(url).query
                parsed_url_query = parse_qs(url_query)
                param_u = parsed_url_query["u"][0]
                encoded_url = param_u[2:]
                encoded_url = encoded_url + '=' * (-len(encoded_url) % 4)
                url = base64.urlsafe_b64decode(encoded_url).decode()

            results.append({'url': url, 'title': title, 'content': content})

            if len(results) >= 10:  # Limit fallback results
                break

    # get number_of_results
    if results:
        result_len_container = "".join(eval_xpath(dom, '//span[@class="sb_count"]//text()'))
        if "-" in result_len_container:
            start_str, result_len_container = re.split(r'-\d+', result_len_container)
            start = int(start_str)
        else:
            start = 1

        result_len_container = re.sub('[^0-9]', '', result_len_container)
        if len(result_len_container) > 0:
            result_len = int(result_len_container)

        expected_start = _page_offset(resp.search_params.get("pageno", 1))

        if expected_start != start:
            if expected_start > result_len:
                # Avoid reading more results than available.
                return []
            # Sometimes Bing will send back the first result page instead of the requested page as a rate limiting
            # measure.
            msg = f"Expected results to start at {expected_start}, but got results starting at {start}"
            raise SearxEngineAPIException(msg)

    results.append({'number_of_results': result_len})
    return results