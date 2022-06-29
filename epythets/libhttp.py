""" Модуль кэширования сетевых документов на диск с парой бонусов в виде подмены User-Agent для обхода защит от ботов"""
import logging
import re
from pathlib import Path

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

cache = None


class Cache:
    user_agent = f'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'

    def __init__(self, path='texts'):
        self.base = Path(path)

    def lookup(self, url: str, ignore_cached=True) -> str:
        """
        :param url: найти в кэше запись по этому URL
        :param ignore_cached: если ничего не найдено - делать запрос и записать его результат, если найдено - падать.
        :return: строка с контентом (пустая в случае игнора кэша)
        """
        cache_file = self._url2file(url)
        if cache_file.is_dir():
            cache_file = cache_file / 'index.html'
        if cache_file.exists():
            logging.debug("Cache hit for url %s %s", url, cache_file)
            if ignore_cached:
                logging.debug("But ignore it because of --ignore-cache")
                return ""
            return cache_file.read_text()
        if not cache_file.parent.exists():
            cache_file.parent.mkdir(parents=True, exist_ok=True)
        resp = self._get(url)
        if cache_file.parent.is_file():
            self._make_directory_with_index(cache_file.parent)
        cache_file.write_text(resp)
        return resp

    def _make_directory_with_index(self, parent):
        """ Хак на случай записи вложенной страницы """
        parent_name = str(parent)
        parent.rename(parent_name + '.tmp')
        tmp_parent = Path(parent_name + '.tmp')
        Path(parent_name).mkdir()
        tmp_parent.rename(parent / 'index.html')

    def _url2file(self, url: str):
        _url = urlparse(url)
        cache_file = self.base / _url.netloc.split(':')[0]  # отсекаем порт
        if _url.path and _url.path != '/':
            cache_file /= _url.path.lstrip('/')
        _query = strip_utm_from_query_string(_url.query)
        if q := re.sub(r'[^A-Za-z0-9]', '', _query):
            cache_file /= q
        return cache_file

    def get(self, url: str, check_cache=True, ignore_cached=True) -> str:
        """
        :param url: URL для проверки
        :param check_cache: вообще заглянуть если у нас что-то в кэше
        :param ignore_cached: если в кэше что-то есть - игнорировать всю запись, но если нет - отправить запрос
        :return:
        """
        if check_cache:
            return self.lookup(url, ignore_cached)
        return self._get(url)

    def _get(self, url: str):
        """
        Прикидываемся мозиллой, некоторые защиты от DDoS не котируют python-requests
        Не хочу делать requests обязательной зависимостью, поэтому динамический ленивый импорт при использовании
        """
        import requests
        resp = requests.get(url, headers={'User-Agent': self.user_agent})
        # Где-то в 5% случаев кириллица нормально не декодится, баг какой-то или хз
        if re.search(r'[А-Яа-я]+', resp.text):
            return resp.text
        return resp.content.decode('utf-8')  # другого выхода всё равно нет, можно не обрабатывать ошибки


def strip_utm_from_query_string(query_string: str) -> str:
    """
    :param query_string: только query_string
    :return: только query_string без UTM-меток
    """
    q = parse_qs(query_string)
    for key in list(q.keys()):
        if key.startswith('utm_'):
            del q[key]
    q = {key: value.pop() if isinstance(value, list) and len(value) == 1 else value for key, value in q.items()}
    return urlencode(q)


def strip_utm(url: str) -> str:
    """
    :param url: URL целиком
    :return: URL целиком, но уже без UTM-меток
    """
    url = urlparse(url)
    _url = list(url)  # тупли неизменяемые
    _url[4] = strip_utm_from_query_string(url.query)  # 4 - индекс в query_string в tuple
    return urlunparse(_url)
