import logging
import sqlite3
from datetime import date
from pathlib import Path

from epythets.mgrep import pick_combos


class Epythet:
    def __init__(self, db, tag=None):
        """ tag по-умолчанию None, чтобы его можно было менять на ходу, переиспользуя объект """
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.tag = tag
        self.today = date.today().strftime("%Y-%m-%d")
        self.url = None

    def process(self, content: str) -> None:
        assert self.tag
        columns = ['tag', 'adjx', 'noun']
        if self.today:
            columns.append('added_at')
        if self.url:
            columns.append('url')
        for n, combo in enumerate(pick_combos(content)):
            adjx, noun = combo
            values = [self.tag, adjx, noun]
            if self.today:
                values.append(self.today)
            if self.url:
                values.append(self.url)
            sql = f"""INSERT OR IGNORE INTO phrase ({', '.join(columns)})
                                VALUES ('{"', '".join(values)}')"""
            self.cur.execute(sql)

    def process_source(self, iterator) -> None:
        """ :param iterator: list or generator of strings (including file descriptors) """
        count = 0
        try:
            for count, line in enumerate(iterator):
                self.process(line)
                if count != 0 and count % 50 == 0:
                    logging.info("PROGRESS: Processed %d lines...", count)
        except UnicodeDecodeError:
            logging.exception("Can't read the fill till the end, line is %d", count)

    def process_file(self, filename: str):
        p = Path(filename)
        assert p.is_file() or p.is_char_device(), f"Can't read {filename}: not a file / char device"
        with p.open() as fd:
            self.process_source(fd)

    def init(self):
        """
        Создаём структуру БД из одной таблицы и вешаем индексы:
        tag: метка. Домен из URL'а, название файла, можно переопределить вручную.
        adjx, noun: Прилагательное и существительное. Уникальное сочетание.
        added_at: Дата добавления в формате 2022-06-06
        url: источник из которого мы взяли эту фразу (для RSS/URL)
        state: Состояние:
            0 - добавлено,
            1 - прикольное надо бы запостить
            2 - уже постили,
            3 - стрёмное для того чтобы постить,
        Номера состояний выбраны с рассчётом выборки для постинга с сортировкой и фильтром.
        Т.е. не больше 2, но чем больше тем лучше.
        """
        self.cur.execute("""CREATE TABLE IF NOT EXISTS "phrase"
            (
                tag text not null,
                adjx text not null,
                noun text,
                added_at text,
                state int default 0 not null,
                url      text,
                constraint phrase_pk
                    primary key (adjx, noun)
            );""")
        for column in 'added_at', 'tag', 'state', 'url':
            self.cur.execute(f"CREATE INDEX phrase_{column}_index on phrase ({column});")
        self.cur.execute("CREATE UNIQUE INDEX phrase_uindex on phrase (adjx, noun);")

    def stat(self):
        logging.info("Database stats:")
        return self.cur.execute(f"SELECT tag, COUNT(1) FROM phrase GROUP BY tag")

    def dump(self):
        sql = f"SELECT adjx || ' ' || noun as p FROM phrase ORDER BY p"
        if self.tag:
            sql = f"SELECT adjx || ' ' || noun as p FROM phrase WHERE tag = '{self.tag}' ORDER BY p"
        return self.cur.execute(sql)
