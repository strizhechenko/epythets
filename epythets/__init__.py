#!/usr/bin/env python3
""" Поиск характерных только для последнего исследуемого текста эпитетов """
# coding: utf-8

import argparse
import logging
from pathlib import Path
from urllib.parse import urlparse

from epythets.libepythet import Epythet
from epythets.parsers import BaseParser


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
    db = Path('.').absolute() / args.db
    if args.db == 'epythets.sqlite':
        logging.warning('Using DB in %s', db)
    if not db.is_file():
        logging.warning("As the DB is not exists yet, initializing it")
        args.init = True
    if args.filename:
        if args.tag is None:
            p = Path(args.filename)
            args.tag = p.name.split('.')[0]
            logging.warning("Hack: setting tag from filename %s", args.tag)
    elif args.url or args.rss or args.mastodon:
        if args.tag is None:
            args.tag = urlparse(args.url or args.rss or args.mastodon).netloc.split(':')[0]  # отсекаем порт
            if args.mastodon and 'api' not in args.mastodon:
                args.mastodon = f'https://{args.tag}/api/v1/timelines/public?local=true'
                logging.warning("Hack: setting mastodon API endpoint from %s to %s", args.tag, args.mastodon)
            logging.warning("Hack: setting tag %s from URL/RSS", args.tag)
    elif args.rss_dive:
        p = BaseParser.from_args(args)
        args.rss_dive = None
        for url in p.parse():
            logging.info("Processing URL: %s", url)
            args.url, args.tag = url, None
            _main(args)
    elif args.tag:
        if not args.dump:
            logging.warning("Hack: reading from stdin, press CTRL-D to skip")
            args.filename = '/dev/stdin'
    elif not any([args.init, args.stat, args.dump]):
        raise AssertionError("You should define --filename, --tag, --stat, --dump or --init")


def _main(args):
    post_parse(args)
    e = Epythet(args.db, args.tag)
    if args.init:
        e.init()
    if args.stat:
        for tag, count in e.stat():
            print(tag, count)
        return
    if args.url or args.rss or args.mastodon:
        e.url = args.url or args.rss
        parser = BaseParser.from_args(args)
        iterator = parser.parse()
        e.process_source(iterator)
    elif args.filename:
        e.today = None  # Сохраняем дату только для обновляемых источников типа RSS
        e.process_file(args.filename)
    if args.dump:
        for phrase in e.dump():
            print(*phrase)
    e.conn.commit()
    e.conn.close()


def main():
    args = parse_args()
    _main(args)
    logging.info("DONE!")


if __name__ == '__main__':
    main()
