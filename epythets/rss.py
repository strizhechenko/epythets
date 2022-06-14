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


def extract_text(xml: str):
    tree = ElementTree.fromstring(xml)
    for channel in tree:
        for item in channel:
            if item.tag == 'item':
                for text in item.findall('title') + item.findall('description'):
                    yield text.text


def from_url(url: str):
    return extract_text(requests_get(url).text)
