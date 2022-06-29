""" Всевозможные парсеры и способы получения текста из разных источников """
import abc
# etree не очень хорошая идея в плане потребления памяти, но RSS вроде не бывают гигантскими.
import json
import logging
import re
from xml.etree import ElementTree

from epythets.libhttp import Cache


class BaseParser:
    cache = True

    def __init__(self, url: str or None, ignore_cache=True):
        """ Если не передать self.url, можно вручную выставить self.content """
        self.content = Cache().get(url, self.cache, ignore_cache) if url else None

    @abc.abstractmethod
    def parse(self) -> list:
        pass

    @staticmethod
    def from_args(args):
        if args.mastodon:
            return MastodonParser(args.mastodon, args.ignore_cache)
        elif args.rss_dive:
            return RSSDiveParser(args.rss_dive, args.ignore_cache)
        elif args.rss:
            return RSSParser(args.rss, args.ignore_cache)
        else:
            return HTMLParser(args.url, args.ignore_cache)


class HTMLParser(BaseParser):
    tags = re.compile(r"<[^>]*>")
    non_cyrillic = re.compile(r'[A-Za-z0-9]+')
    symbols = re.compile(r"[\"'{\}_\[/=\\()@|]")
    spaces = re.compile(r"[ ]{2,}")

    def parse(self):
        """ Выполняется снизу вверх """
        return self.spaces.sub(
            ' ', self.symbols.sub(
                ' ', self.non_cyrillic.sub(
                    ' ', self.tags.sub(
                        ' ', self.content)))
        ).splitlines()


class RSSParser(BaseParser):
    cache = False
    atom = "{http://www.w3.org/2005/Atom}"

    def make_tree(self):
        try:
            return ElementTree.fromstring(self.content)
        except ElementTree.ParseError:
            logging.exception("XML: %s", self.content)
            raise

    def parse(self):
        """ Генератор, возвращающий заголовки и описания из ленты RSS """
        tree = self.make_tree()
        yield from self.parse_atom(tree) if self.atom in tree.tag else RSSParser.parse_rss(tree)

    @staticmethod
    def parse_rss(tree):
        """ Обрабатываем классический RSS """
        for channel in tree:
            for item in channel.findall('item'):
                for text in item.findall('title') + item.findall('description'):
                    yield text.text

    def parse_atom(self, tree):
        """ Обарабатываем Atom-feed"""
        for entry in tree.findall(self.atom + "entry"):
            for text in entry.findall(self.atom + 'title') + entry.findall(self.atom + 'content'):
                yield text.text


class RSSDiveParser(RSSParser):
    def parse(self):
        """ Парсер возвращает не текст, а ссылки на статьи из RSS-ленты """
        tree = self.make_tree()
        for channel in tree:
            for item in channel:
                if item.tag == 'item':
                    for link in item.findall('link'):
                        yield link.text


class MastodonParser(HTMLParser):
    cache = False

    def parse(self):
        """ Здесь, несмотря на то что казалось бы можно requests.json() это неудобно """
        htmlparser = HTMLParser(None)
        data = json.loads(self.content)
        logging.debug("Fetched %d items", len(data))
        for toot in data:
            if not toot.get('content'):
                continue
            htmlparser.content = toot['content']
            for content in htmlparser.parse():
                if text := content.replace("'", "").strip():
                    yield text
