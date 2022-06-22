import abc
# etree не очень хорошая идея в плане потребления памяти, но RSS вроде не бывают гигантскими.
import json
import logging
from xml.etree import ElementTree

from epythets.http import Cache


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
    def __init__(self, url, ignore_cache=True):
        """ Тоже хаки, чтобы не делать html2text обязательной зависимостью, но и не плодить объекты пачками """
        super().__init__(url, ignore_cache)
        from html2text import HTML2Text
        h = HTML2Text()
        h.ignore_images = h.ignore_links = h.ignore_tables = True
        self.h = h

    def parse(self):
        """ Не очень-то и HTML2Text обязательно тащить. Потом в плагины вынесу. """
        return self.h.handle(self.content).splitlines()


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
