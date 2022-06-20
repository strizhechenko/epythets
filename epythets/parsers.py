import logging
import abc
# etree не очень хорошая идея в плане потребления памяти, но RSS вроде не бывают гигантскими.
import json
from xml.etree import ElementTree

from epythets.http import requests_get


class BaseParser:
    cache = True

    def __init__(self, url: str or None):
        """ Если не передать self.url, можно вручную выставить self.content """
        self.url = url
        self.content = requests_get(self.url, self.cache) if self.url else None

    @abc.abstractmethod
    def parse(self) -> list:
        pass

    @staticmethod
    def from_args(args):
        if args.mastodon:
            return MastodonParser(args.mastodon)
        elif args.rss_dive:
            return RSSDiveParser(args.rss_dive)
        elif args.rss:
            return RSSParser(args.rss)
        else:
            return HTMLParser(args.url)


class HTMLParser(BaseParser):
    def __init__(self, url):
        """ Тоже хаки, чтобы не делать html2text обязательной зависимостью, но и не плодить объекты пачками """
        super().__init__(url)
        from html2text import HTML2Text
        h = HTML2Text()
        h.ignore_images = h.ignore_links = h.ignore_tables = True
        self.h = h

    def parse(self):
        """ Не очень-то и HTML2Text обязательно тащить. Потом в плагины вынесу. """
        return self.h.handle(self.content).splitlines()


class RSSParser(BaseParser):
    cache = False

    def make_tree(self):
        try:
            return ElementTree.fromstring(self.content)
        except ElementTree.ParseError:
            logging.exception("XML: %s", self.content)
            raise

    def parse(self):
        """ Генератор, возвращающий заголовки и описания из ленты RSS """
        atom = "{http://www.w3.org/2005/Atom}"
        tree = self.make_tree()
        if atom in tree.tag:
            for entry in tree.findall(atom + "entry"):
                for text in entry.findall(atom + 'title') + entry.findall(atom + 'content'):
                    yield text.text
        else:
            for channel in tree:
                for item in channel.findall('item'):
                    for text in item.findall('title') + item.findall('description'):
                        yield text.text


class RSSDiveParser(RSSParser):
    def parse(self):
        """ Парсер возвращает не текст, а ссылки на статьи из RSS-ленты """
        tree = self.make_tree()
        for channel in tree:
            for item in channel:
                if item.tag == 'item':
                    processed = False
                    for link in item.findall('link'):
                        processed = True
                        yield link.text
                    if processed:
                        continue
                    for guid in item.findall('guid'):
                        if guid.attrib.get('isPermaLink'):
                            yield link.text  # TODO: понять, актуально ли и не баг ли копипасты, вроде хабровский RSS


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

