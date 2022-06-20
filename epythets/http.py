import logging
import re
from pathlib import Path
from urllib.parse import urlparse


def requests_get(url: str, cache=True) -> str:
    return _cache_get(url) if cache else _requests_get(url)


def _requests_get(url: str):
    """
    Прикидываемся мозиллой, некоторые защиты от DDoS не котируют python-requests
    Не хочу делать requests обязательной зависимостью, поэтому динамический ленивый импорт при использовании
    """
    import requests
    user_agent = f'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'
    return requests.get(url, headers={'User-Agent': user_agent}).text


def _cache_get(url: str):
    cache_file = _url_to_cache(url)
    if cache_file.exists():
        logging.info("Cache hit for url %s %s", url, cache_file)
        return cache_file.read_text()
    if not cache_file.parent.exists():
        cache_file.parent.mkdir(parents=True, exist_ok=True)
    resp = _requests_get(url)
    cache_file.write_text(resp)
    return resp


def _url_to_cache(url: str):
    """ TODO: отрезать UTM-метки"""
    _url = urlparse(url)
    cache_file = Path('texts') / _url.netloc.split(':')[0]  # отсекаем порт
    if _url.path and _url.path != '/':
        cache_file /= _url.path.lstrip('/')
    if q := re.sub(r'[^A-Za-z0-9]', '', _url.query):
        cache_file /= q
    return cache_file
