import logging
from unittest import TestCase

from epythets.mgrep import pick_combos


class TestMgrep(TestCase):
    def setUp(self) -> None:
        logging.basicConfig(level=logging.INFO, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

    def _check_it(self, line, expected, word_count=3):
        self.assertEqual(expected, list(" ".join(combo) for combo in pick_combos(line, word_count=word_count)))

    def test_it(self):
        self._check_it("своих старых", [], word_count=2)
        self._check_it("просто набор", [], word_count=2)
        self._check_it("гадкий я", [], word_count=2)  # игнорируем слова короче двух букв
        self._check_it("гадкий ты", [], word_count=2)  # игнорируем слова короче трёх букв
        self._check_it("неправильные схемы", ["Неправильные Схемы"], word_count=2)  # сохраняем согласованное число
        # После добавления динамического языка шаблонов исчезла фича приведения фразы в норму.
        # self._check_it("по крайней мере", ["Крайняя Мера"], word_count=2)  # но при этом склоняем в именительный падеж
        self._check_it("согласованные словосочетания", ["Согласованные Словосочетания"],
                       word_count=2)  # поддерживаем причастия
        self._check_it("мудень проотвеченный", [],
                       word_count=2)  # порядок строго прилагательное-существительное, а не наоборот
        self._check_it("достаточно длинная строка для проверки итерации", ["Длинная Строка"], word_count=2)
        self._check_it("Приглушённые Детские", [],
                       word_count=2)  # не принимаем последовательные прилагательные за существительные
        self._check_it("Человекочитаемый язык", ["Человекочитаемый Язык"], word_count=2)  # не искажаем залоги причастий
        # adjf_adjf_noun
        self._check_it("Специальный налоговый режим", ["Специальный Налоговый Режим"], word_count=3)
        # Удар мощный, здоровья сносит примерно как выпад != Мощный здоровье
        # атакующие чудеса брать не рекомендуется != Атаковавшие Чуда
        # атаки с Большим молотом гирмов != Молотый Гирм
        # adjf_noun_noun
        self._check_it("российское импортозамещение программ", ["Российское Импортозамещение Программ"])
        self._check_it("Прикормленный Исполнитель Госзаказа", ["Прикормленный Исполнитель Госзаказа"], word_count=3)
        # noun_adjf_noun
        self._check_it("Заместитель генерального директора", ["Заместитель Генерального Директора"])
        # _line = "Это встревожило Неревара ещё больше" -> не должно срабатывать
        # _line = "Технические Условия Являются" -> глаголы не должны просачиваться
        # _line = "Мразотные Стороны Человека" -> при повышении границы score может легко пропасть
        # мотивы надзорных жалобы или представления и вынесения постановления ->
        # кажется adjf:gent noun:gent без согласования числа работает
