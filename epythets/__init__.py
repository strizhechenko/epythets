#!/usr/bin/env python3
""" Поиск характерных только для последнего исследуемого текста эпитетов """
# coding: utf-8

import argparse
import logging
from pathlib import Path
from urllib.parse import urlparse

from epythets.libepythet import Epythet
from epythets.parsers import BaseParser
from epythets.libhttp import strip_utm


def parse_args():
    """ Разбор аргументов"""
    parser = argparse.ArgumentParser()
    parser.description = "Вытянуть последние N записей из мастодон в свой SQLite для фразочек бота"
    parser.add_argument('--filename', type=str, help='Путь к текстовому файлу')
    parser.add_argument('--url', type=str, help='Использовать вместо файла HTML со страницы')
    parser.add_argument('--mastodon', type=str, help='Использовать вместо файла публичный API инстанса мастодон')
    parser.add_argument('--rss', type=str, help='Использовать вместо файла заголовки и описания из RSS-фида')
    parser.add_argument('--rss-dive', type=str, help='Использовать вместо файла содержимое всех статей из RSS-фида')
    parser.add_argument('--db', type=str, help='БД для сохранения фразочек', default='epythets.sqlite')
    parser.add_argument('--tag', type=str, help='Метка источника для добавляемых фраз')
    parser.add_argument('--init', action='store_true', help="Создать БД")
    parser.add_argument('--stat', action='store_true', help="Статистика по меткам в БД")
    parser.add_argument('--dump', action='store_true', help="Извлечь данные из БД")
    parser.add_argument('--re-read', action='store_false', dest='ignore_cache', default=True,
                        help="Не читать кэшированные данные")
    parser.add_argument('--debug', action='store_true', default=False, help="Включить отладочное логирование.")
    parser.add_argument('--silent', action='store_true', default=False, help="Оставить только warning/error логи.")
    args = parser.parse_args()
    # A little trick: setting logging up as soon as possible to be able to use it in argument validation
    level = logging.DEBUG if args.debug else logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(level=level, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(levelname)s %(message)s")
    return args


def post_parse(args: argparse.Namespace):
    """ Стараемся _вывести_ недостающие аргументы из имеющихся, дефолты, удобство и т.д. """
    database = Path('.').absolute() / args.db
    if args.db == 'epythets.sqlite':
        logging.debug('Using DB in %s', database)
    if not database.is_file():
        logging.info("As the DB %s is not exists yet, initializing it", args.db)
        args.init = True
    if args.filename:
        url, tag = Path(args.filename).name.split('.')[0], 'local_files'
        if args.tag is None:
            args.tag = tag
        if args.url is None:
            args.url = url
        logging.debug("Hack: setting tag %s / url %s from filename %s", args.tag, args.url, args.filename)
    elif args.url or args.rss or args.mastodon:
        if args.tag is None:
            args.tag = tag_from_url(args)
    elif args.rss_dive:
        path = BaseParser.from_args(args)
        args.rss_dive = None
        for url in path.parse():
            logging.info("Processing URL: %s", url)
            args.url, args.tag = url, None
            _main(args)
    elif args.tag:
        if not args.dump:
            logging.info("Hack: reading from stdin, press CTRL-D to skip")
            args.filename = '/dev/stdin'
    elif not any([args.init, args.stat, args.dump]):
        raise AssertionError("You should define --filename, --tag, --stat, --dump or --init")


def tag_from_url(args):
    """ На основании одного из URL-флагов вычисляем недостающий тег для записей """
    tag = urlparse(args.url or args.rss or args.mastodon).netloc.split(':')[0]  # отсекаем порт
    if args.mastodon and 'api' not in args.mastodon:
        args.mastodon = f'https://{tag}/api/v1/timelines/public?local=true'
        logging.debug("Hack: setting mastodon API endpoint from %s to %s", tag, args.mastodon)
    if tag.startswith('www'):
        tag = tag[4:]
    logging.debug("Hack: setting tag %s from URL/RSS", tag)
    return tag


def _main(args):
    """ Основная логика прграммы, которая может быть использована в других программах с подставными аргументами """
    post_parse(args)
    epythet = Epythet(args.db, args.tag)
    if args.init:
        epythet.init()
    if args.stat:
        for tag, count in epythet.stat():
            print(tag, count)
        return
    if (args.url or args.rss or args.mastodon) and not args.filename:  # скармливание файла выставляет его имя в URL
        epythet.url = strip_utm(args.url or args.rss)
        parser = BaseParser.from_args(args)
        iterator = parser.parse()
        epythet.process_source(iterator)
    elif args.filename:
        epythet.url = args.url
        epythet.process_file(args.filename)
    if args.dump:
        for phrase in epythet.dump():
            print(*phrase)
    epythet.conn.commit()
    epythet.conn.close()


def main():
    """ Основное поведение утилиты, парсит аргументы, а дальше всё стандартно """
    args = parse_args()
    _main(args)
    logging.debug("DONE!")


if __name__ == '__main__':
    main()
