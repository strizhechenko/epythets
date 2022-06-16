# etree не очень хорошая идея в плане потребления памяти, но RSS вроде не бывают гигантскими.
from xml.etree import ElementTree


def requests_get(url):
    """
    Прикидываемся мозиллой, некоторые защиты от DDoS не котируют python-requests
    Не хочу делать requests обязательной зависимостью, поэтому динамический ленивый импорт при использовании
    """
    import requests
    user_agent = f'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'
    return requests.get(url, headers={'User-Agent': user_agent})


def parse_rss(xml: str):
    tree = ElementTree.fromstring(xml)
    for channel in tree:
        for item in channel:
            if item.tag == 'item':
                for text in item.findall('title') + item.findall('description'):
                    yield text.text


def parse_html(html: str):
    """ Не очень-то и HTML2Text обязательно тащить. Потом в плагины вынесу. """
    from html2text import HTML2Text
    h = HTML2Text()
    h.ignore_images = h.ignore_links = h.ignore_tables = True
    return h.handle(html).splitlines()


def from_url(url: str, rss=True):
    return (parse_rss if rss else parse_html)(requests_get(url).text)


def get_urls(rss_url: str):
    xml = requests_get(rss_url).text
    tree = ElementTree.fromstring(xml)
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
                        yield link.text
