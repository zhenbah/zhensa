# SPDX-License-Identifier: AGPL-3.0-or-later
"""Baidu Shopping
"""

from urllib.parse import urlencode
from datetime import datetime
from html import unescape
import time
import json

from searx.exceptions import SearxEngineAPIException, SearxEngineCaptchaException
from searx.utils import html_to_text

about = {
    "website": "https://www.baidu.com",
    "wikidata_id": "Q14772",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
    "language": "zh",
}

paging = True
categories = ["shopping"]
results_per_page = 10

time_range_support = True
time_range_dict = {"day": 86400, "week": 604800, "month": 2592000, "year": 31536000}


def init(_):
    pass


def request(query, params):
    page_num = params["pageno"]

    # Baidu shopping search URL
    endpoint = 'https://www.baidu.com/s'
    params_url = {
        "wd": query,
        "rn": results_per_page,
        "pn": (page_num - 1) * results_per_page,
        "tn": "json",
        "rsv_spt": "1",  # shopping parameter
        "rsv_dl": "0_right_recom_21102_1",  # shopping related
    }

    if params.get("time_range") in time_range_dict:
        now = int(time.time())
        past = now - time_range_dict[params["time_range"]]
        params_url["gpc"] = f"stf={past},{now}|stftype=1"

    params["url"] = f"{endpoint}?{urlencode(params_url)}"
    params["allow_redirects"] = False
    return params


def response(resp):
    # Detect Baidu Captcha, it will redirect to wappass.baidu.com
    if 'wappass.baidu.com/static/captcha' in resp.headers.get('Location', ''):
        raise SearxEngineCaptchaException()

    text = resp.text
    data = json.loads(text, strict=False)

    results = []
    if not data.get("feed", {}).get("entry"):
        raise SearxEngineAPIException("Invalid response")

    for entry in data["feed"]["entry"]:
        if not entry.get("title") or not entry.get("url"):
            continue

        published_date = None
        if entry.get("time"):
            try:
                published_date = datetime.fromtimestamp(entry["time"])
            except (ValueError, TypeError):
                published_date = None

        # title and content sometimes containing characters such as & ' " etc...
        title = unescape(entry["title"])
        content = unescape(entry.get("abs", ""))

        results.append(
            {
                "title": title,
                "url": entry["url"],
                "content": content,
                "publishedDate": published_date,
            }
        )
    return results