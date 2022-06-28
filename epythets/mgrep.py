""" По сути ядро программы - модуль морфологического матчинга по шаблону """
# coding: utf-8
import logging
import re
from copy import deepcopy
from functools import lru_cache

from pymorphy2 import MorphAnalyzer

from epythets.patterns import patterns

morpher = MorphAnalyzer()
IGNORE_WORDS = {
    'весь', 'всё', 'её', 'каждый', 'какой', 'никакой', 'такой', 'который', 'мой', 'он', 'они', 'твой', 'то', 'тот',
    'это', 'этот', 'сам', 'свой', 'другой', 'иной', 'наш', 'любой', 'один', 'всякий', 'многие', 'некоторый', 'чей',
    'самый', 'сей', 'данный', 'некий', 'ваш', 'новый', 'разный'
}

WORD_SEP = re.compile(r'[ \t\n]+')
PHRASE_SEP = re.compile(r'[,.!?;-]+')
LONG_RU = re.compile('^[а-я]{3,}$')


@lru_cache(200000)
def parse(word):
    return [w for w in morpher.parse(word) if w.score > 0.03]


def common(word1, word2, tags, deep=0):
    logging.debug("%sLook for common %s between %s and %s", ' ' * deep, tags, word1[0].word, word2[0].word)
    if isinstance(tags, str):
        return _common_str(word1, word2, tags, deep + 1)
    if isinstance(tags, dict):
        return _common_dict(word1, word2, tags, deep + 1)
    raise NotImplementedError("Не поддерживается тип тэгов", type(tags), tags)


def _common_dict(word1, word2, tags, deep=0):
    for key, value in tags.items():
        if isinstance(value, list):
            return _common_list(word1, word2, key, value, deep + 1)
        raise NotImplementedError("Не поддерживается субтип тэгов", type(value))


def _common_list(word1, word2, key, value, deep=0):
    if key == 'AND':
        return _common_and(word1, word2, value, deep + 1)
    elif key == 'OR':
        return _common_or(word1, word2, value, deep + 1)
    raise NotImplementedError("Не поддерживается операнд", key)


def _common_or(word1, word2, value, deep=0):
    for v in value:
        res = common(word1, word2, v, deep + 1)
        if res:
            return res
    return False


def _common_and(word1, word2, value, deep=0):
    for v in value:
        res = common(word1, word2, v, deep + 1)
        if not res:
            logging.debug("%sAND COMMON failed %s %s %s", ' ' * deep, v, word1, word2)
            return False
        word1, word2 = res
    return word1, word2


def _common_str(word1, word2, tags, deep=0):
    w1, w2 = list(), list()
    for word in word1:
        if tags in word.tag:
            logging.debug("%sw1: %s", ' ' * deep, word)
            w1.append(word)
    for word in word2:
        if tags in word.tag:
            logging.debug("%sw2: %s", ' ' * deep, word)
            w2.append(word)
    if not all((w1, w2)):
        logging.debug("%sOne of the words is empty: %s %s", ' ' * deep, w1, w2)
        return False
    return w1, w2


def tag_match(parsed, tags, deep=0):
    logging.debug("%sTAG MATCH %s against %s", ' ' * deep, tags, parsed)
    if isinstance(tags, str):
        w1 = list()
        for word in parsed:
            if tags in word.tag:
                w1.append(word)
        logging.debug("%sTAG MATCH RESULT: %s against %s", ' ' * deep, tags, w1)
        return w1
    if isinstance(tags, dict):
        for key, value in tags.items():
            if key == 'OR':
                return any(tag_match(parsed, tag, deep + 1) for tag in value)
            elif key == 'ALL':
                return all(tag_match(parsed, tag, deep + 1) for tag in value)
            return NotImplementedError("Не поддерживается оператор", key)
    raise NotImplementedError("Не поддерживается тип тэга", type(tags))


def match_word(words: list, word: list, rule: str or tuple or dict, deep=0) -> bool:
    """
    :param words: список остальных слов в потенциальной фразе. Нужен для удобства ссылок в COMMON/WITH
    :param word: список вариантов распарсивания слова
    :param rule: правила, которому слово должно соответствовать
    :param deep: глубина вызова (для выравнивания логирования)
    """
    while rule:
        logging.debug("%sMatching rules %s (%s)", ' ' * deep, type(rule), rule)
        if isinstance(rule, str):
            if rule == 'IGNORED':
                logging.debug("%sCHECK IGNORED for %s", ' ' * deep, word)
                return is_ignored(word)
            raise NotImplementedError(rule)
        elif isinstance(rule, tuple) and len(rule) == 2:
            operator, operands = rule
            logging.debug("%sOPERATOR: %s OPERANDS: %s", ' ' * deep, operator, operands)
            if operator == 'NOT':
                return not match_word(words, word, operands, deep + 1)
            if operator == 'COMMON':
                against = words[operands['WITH']]
                c = common(word, against, operands['TAG'], deep + 1)
                logging.debug("%sCOMMON returned %s", ' ' * deep, c)
                return c
            if operator == 'TAG':
                return tag_match(word, operands, deep + 1)
            raise NotImplementedError(operator)
        elif isinstance(rule, dict):
            if not match_word(words, word, rule.popitem(), deep + 1):
                return False
        else:
            raise NotImplementedError("Unknown prop type", type(rule), rule)
    return True


def is_ignored(parsed):
    if parsed[0].normal_form in IGNORE_WORDS:
        logging.debug("Нормальная форма слова %s в блэклисте", parsed[0])
        return True
    if parsed[0].word in IGNORE_WORDS:
        logging.debug("Слово %s в блэклисте", parsed[0])
        return True
    return False


def match_phrase(words: list or tuple) -> list:
    failed = [None] * len(words)
    if not all(map(LONG_RU.match, words)):
        return failed
    _words = list(map(parse, words))
    if not all(_words):
        logging.debug("Часть слов не распарсилась %s", _words)
        return failed
    logging.debug("WORDS: %s", words)
    for word in _words:
        logging.debug("WORD: %s", word)
    _patterns = deepcopy(patterns[len(words)])
    for ptrn in _patterns:
        logging.debug("-------------------- Trying to match '%s' against...", " ".join(words))
        matched = False
        for n, rule in enumerate(ptrn):
            logging.debug("%d: %s : %s", n, words[n], rule)
            if not match_word(_words, _words[n], rule):
                matched = False
                logging.debug("FAILED: rule %d: %s on %s", n, rule, _words[n])
                break
            matched = True
        if matched:
            return words
    return failed


def pick_combos(line: str, function=match_phrase, word_count=3) -> tuple:
    """
    Точка входа в библиотеку.
    :param word_count: число слов в шаблоне
    :param function: функция для валидации и нормализации слов
    :param line: просто строка текста. Хоть целую книгу можно сюда засунуть.
    :return: подходящие под заданный шаблон пары слов
    """
    for phrase in PHRASE_SEP.split(line.lower()):
        words = WORD_SEP.split(phrase)
        for n, word in enumerate(words[:-word_count + 1]):
            if all(result := function(words[n:n + word_count])):
                yield map(str.capitalize, result)


def main():
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
    s3 = set()
    from pathlib import Path
    for file in Path('../texts/www.linux.org.ru/news/opensource/').iterdir():
        with file.open() as fd:
            for _line in fd:  # sys.stdin
                for _i in pick_combos(_line, match_phrase, 3):
                    s3.add(tuple(_i))
    for i in sorted(s3):
        logging.info("Гарри Поттер и %s %s %s", *i)


if __name__ == '__main__':
    main()
