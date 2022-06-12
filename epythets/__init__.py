#!/usr/bin/env python3
""" Поиск характерных только для последнего исследуемого текста эпитетов """
# coding: utf-8

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from epythets.mgrep import pick_combos


def parse_args():
    """ Разбор аргументов"""
    parser = argparse.ArgumentParser()
    parser.description = "Вытянуть последние N записей из мастодон в свой SQLite для фразочек бота"
    parser.add_argument('--filename', type=str, help='Путь к текстовому файлу')
    parser.add_argument('--db', type=str, help='БД для сохранения фразочек', default='epythets.sqlite')
    parser.add_argument('--label', type=str, help='Пометка источника для добавляемых фраз')
    parser.add_argument('--init', action='store_true', help="Создать БД")
    parser.add_argument('--stat', action='store_true', help="Статистика по меткам в БД")
    parser.add_argument('--dump', action='store_true', help="Извлечь данные из БД")
    parser.add_argument('--debug', action='store_true', default=False, help="Включить отладочное логирование.")
    parser.add_argument('--silent', action='store_true', default=False, help="Оставить только warning/error логи.")
    args = parser.parse_args()
    # A little trick: setting logging up as soon as possible to be able to use it in argument validation
    level = logging.DEBUG if args.debug else logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(level=level, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
    db = Path('.').absolute() / args.db
    if args.db == 'epythets.sqlite':
        logging.warning('Using DB in %s', db)
    if not db.is_file():
        logging.warning("As the DB is not exists yet, initializing it")
        args.init = True
    if args.filename:
        if args.label is None:
            logging.warning("Hack: setting label from filename")
            p = Path(args.filename)
            args.label = p.name.split('.')[0]
    elif args.label:
        if not args.dump:
            logging.warning("Hack: reading from stdin, press CTRL-D to skip")
            args.filename = '/dev/stdin'
    elif not args.init and not args.stat:
        raise AssertionError("You should define --filename, --label, --stat or --init")
    return args


def process(label, content, cur):
    for n, combo in enumerate(pick_combos(content)):
        cur.execute(f"INSERT OR IGNORE INTO phrase (label, phrase) VALUES ('{label}', '{combo}')")


def init(cur):
    cur.execute("""create table phrase
        (
            phrase  text not null constraint phrase_pk primary key,
            posted  int default 0 not null,
            label text not null
        );""")
    cur.execute("create unique index phrase_phrase_uindex on phrase (phrase);")


def main():
    args = parse_args()
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    if args.init:
        init(cur)
    if args.stat:
        logging.info("Database stats:")
        for label, count in cur.execute(f"SELECT label, COUNT(DISTINCT phrase) FROM phrase GROUP BY label").fetchall():
            logging.info('Label %s: %d phrases', label, count)
        return
    if args.filename:
        p, count = Path(args.filename), 0
        if p.is_file() or p.is_char_device():
            with p.open() as fd:
                try:
                    for count, line in enumerate(fd):
                        process(args.label, line, cur)
                        if count % 50 == 0:
                            logging.info("PROGRESS: Processed %d lines...", count)
                except UnicodeDecodeError:
                    logging.exception("Can't read the fill till the end, line is %d", count)
    if args.dump:
        for phrase in cur.execute(f"SELECT phrase FROM phrase WHERE label = '{args.label}' ORDER BY phrase").fetchall():
            print(phrase[0])
        return
    conn.commit()
    conn.close()
    logging.info("DONE!")


if __name__ == '__main__':
    main()
