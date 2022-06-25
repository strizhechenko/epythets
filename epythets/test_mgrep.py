import logging
from unittest import TestCase

from epythets.mgrep import pick_combos


class TestMgrep(TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

    def _check_it(self, line, expected):
        self.assertEqual(expected, list(" ".join(combo) for combo in pick_combos(line)))

    def test_it(self):
        self._check_it("своих старых", [])
        self._check_it("просто набор", [])
        self._check_it("гадкий я", [])  # игнорируем слова короче двух букв
        self._check_it("неправильные схемы", ["Неправильные Схемы"])  # сохраняем согласованное число
        self._check_it("по крайней мере", ["Крайняя Мера"])  # но при этом склоняем в именительный падеж
        self._check_it("согласованных словосочетаний", ["Согласованные Словосочетания"])  # поддерживаем причастия
        self._check_it("мудень проотвеченный", [])  # порядок строго прилагательное-существительное, а не наоборот
        self._check_it("достаточно длинная строка для проверки итерации", ["Длинная Строка"])
        self._check_it("Приглушённые Детские", [])  # не принимаем последовательные прилагательные за существительные
        self._check_it("Человекочитаемый язык", ["Человекочитаемый Язык"])  # не искажаем залоги причастий
        # Удар мощный, здоровья сносит примерно как выпад != Мощный здоровье
        # атакующие чудеса брать не рекомендуется != Атаковавшие Чуда
        # атаки с Большим молотом гирмов != Молотый Гирм
