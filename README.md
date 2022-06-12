# epythets

С помощью pymorphy извлекаем, нормализуем из текста множество эпитетов, сохраняя их в sqlite.

## Зачем?

Так можно извлечь специфические эпитеты и неологизмы из текста для дальнейшего использования.

## Зачем-зачем?

[Затем](https://cpad.ask.fm/af3/4b0f5/ddc1/4880/929c/e8709d71dd60/large/2821587.jpg).

## Эпитеты?

Словосочетания соответствующие шаблону

`< прилагательное | причастие в страдательном залоге > < существительное >`

при этом оба слова изначально согласованы по числу и полу. Перед сохранением оба слова приводятся в именительный падеж.

## Как использовать

### Установка

Из pypi:

``` shell
sudo pip3 install epythets
```

[Альтернативые способы](/README_full.md).

#### Совместимость

Поддерживается только python3.8+. Если хочется что-то старее - можно форкнуть, поправить в `mgrep.py` единственное использование `:=` на две отдельные строчки и установить из исходников.

### Обучение

БД будет инициализирована в файле epythets.sqlite в текущей директории при первом запуске, если этого файла ещё нет. Путь можно переопределить параметром `--db /your/db.sqlite`, но его придётся указывать для каждого скармливаемого файла.

"Обучаем" на классике, чтобы типовые обороты не считались спецификой последующих текстов. На самом деле одного "Идиота" для этого мало - ~2.8к фраз. Метка (label) "idiot" внутри БД будет автоматически вычислена из имени файла.

``` shell
epythets --filename texts/idiot.txt
```

Дообучим на нескольких произведениях Говарда Филиппса Лавкрафта. Из "Случая Чарльза Декстера Уальда" извлеклось около 2 500 фраз, а из "Хребтов Безумия" - 1 500, при значительно меньших длинах текста.

В этом примере используется альтернативный подход с флагами утилиты - метку указываем явно, а файл читаем с stdin.

``` shell
epythets --label 'wild' < texts/wild.txt
epythets --label 'madness' < texts/at_the_mountains_of_madness.txt
```

"Шлифанём" "Снами в Ведьмином Доме" - 662 фразы, но поскольку мы неплохо "обучились" ранее около 40-60% извлечённых фраз являются довольно-таки специфичными для этого произведения. Что и было моей исследовательской целью. Если увеличить объём первичного обучения, выйдет ещё точнее.

``` shell
epythets --filename texts/witchhouse.txt
```

### Просмотр результатов

Копаемся себе в извлечённых фразах:

``` shell
epythets --label=witchhouse --dump
```

- Современная Работа
- Замкнутое Пространство
- Детские Кости
- Скрытый Страх
- Другая Находка
- Странные Умолчания
- Скупые Сведения
- Пятипалые Лапки
- Маленький Череп
- Режущий Слух
- ...

Как посмотреть статистику по файлам (сколько эпитетов из какого текста извлечено):

``` shell
epythets --stat
```

| label | count |
| :--- | ---: |
| ilf_petrov:12_chairs | 3891 |
| gogol:viy | 243 |
| platon:gosudarstvo | 322 |
| dostoevsky:idiot | 2271 |
| lovecraft:madness |1385 |
| lovecraft:wild |1334 |
| lovecraft:witchhouse | 615 |
| limstin_python:fun_in_morrowind | 1362 |
