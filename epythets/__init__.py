#!/usr/bin/env python3
""" Поиск характерных только для последнего исследуемого текста эпитетов """
# coding: utf-8

import argparse
import logging
import sqlite3
from pathlib import Path

from epythets.mgrep import pick_combos


def parse_args():
    """ Разбор аргументов"""
    parser = argparse.ArgumentParser()
    parser.description = "Вытянуть последние N записей из мастодон в свой SQLite для фразочек бота"
    parser.add_argument('--filename', type=str, help='Путь к текстовому файлу')
    parser.add_argument('--db', required=True, type=str, help='БД для сохранения фразочек')
    parser.add_argument('--label', type=str, help='Пометка источника для добавляемых фраз')
    parser.add_argument('--init', action='store_true', help="Создать БД")
    parser.add_argument('--debug', action='store_true', default=False, help="Включить отладочное логирование.")
    parser.add_argument('--silent', action='store_true', default=False, help="Оставить только warning/error логи.")
    args = parser.parse_args()
    assert (args.filename is None and args.label is None) or all((args.filename, args.label))
    return args


def process(label, content, cur):
    n = 0
    for n, combo in enumerate(pick_combos(content)):
        cur.execute(f"INSERT OR IGNORE INTO phrase (label, phrase) VALUES ('{label}', '{combo}')")
    if n > 10:
        logging.info("Processed line with %d phrases", n)


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
    logging.basicConfig(level=(logging.DEBUG if args.debug else logging.WARNING if args.silent else logging.INFO),
                        format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")
    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    if args.init:
        init(cur)
    if not args.filename:
        exit(0)
    p, count = Path(args.filename), 0
    assert p.is_file()
    with p.open() as fd:
        try:
            for count, line in enumerate(fd):
                process(args.label, line, cur)
                if count % 50 == 0:
                    logging.info("Processed %d lines...", count)
        except UnicodeDecodeError:
            logging.exception("Can't read the fill till the end, line is %d", count)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
