# Sprawozdanie — Zestaw zaliczeniowy AAP

**Autor:** Dawid Giza
**Przedmiot:** Architektura Aplikacji w Pythonie (WSEI Kraków, semestr letni 2026)
**Dataset:** `stanfordnlp/imdb` (50 000 recenzji filmów z etykietą sentymentu pos/neg)

---

## Środowisko

- **Platforma:** Google Colab (Linux, Python 3.12)
- **Rdzenie:** `os.cpu_count() = 2` (istotne dla Lab 2 — patrz insight)
- **Kluczowe pakiety:** `datasets`, `pandas`, `pyspark 4.0.3`, `matplotlib`, `scikit-learn`, `pytest`
- **Uruchomienie:** komórka instalacyjna na górze (`!pip install -q datasets pyspark`), następnie *Runtime → Run all*. Dataset pobiera się raz z Hugging Face Hub i jest cache'owany.
- **Powtarzalność:** próbki pobierane przez `get_imdb_subset()` z `.shuffle(seed=42)` — bez tego dataset (zsortowany po labelu) dałby 100% jednej klasy.

---

## Lab 1 — Dekoratory (`@retry` + `@cache_to_disk`)

**Co zrobiłem:** dwa dekoratory produkcyjnej jakości. `@retry` ponawia wywołanie z **exponential backoff** (`delay * backoff**próba`), `@cache_to_disk` zapisuje wynik do JSON pod kluczem `md5(repr(args))` i przy drugim wywołaniu czyta z dysku bez wykonywania funkcji.

**Wynik:** dla `flaky_fetch` (50% szansy błędu) i `max_attempts=5`: empirycznie **96–100/100 sukcesów**, teoria `P = 1 − 0.5^5 = 0.969`. Cache hit ~0.5 ms.

**Insight:** szansa sukcesu rośnie geometrycznie z liczbą prób (`1 − 0.5^N`): 1 próba = 50%, 3 = 87.5%, 5 = 96.9%. Empiria pokrywa się z teorią. Kolejność dekoratorów ma znaczenie — `@cache_to_disk` jest **na zewnątrz** `@retry`, więc najpierw sprawdzamy cache, a dopiero przy jego braku odpalamy mechanizm ponawiania (cache'owanie udanego wyniku eliminuje przyszłe retry).

---

## Lab 2 — Współbieżność (sekwencyjnie vs ThreadPool vs multiprocessing)

**Co zrobiłem:** funkcja `sentiment_score` (lexicon-based), porównanie 3 implementacji na tych samych 5000 recenzji + wykres słupkowy. Aby zadanie było realnie CPU-bound, scoring powtarzany `REPEAT=60` razy; do procesów potomnych przekazywane są **tylko indeksy** (teksty dziedziczone globalnie przez `fork`) — minimalizacja narzutu IPC.

**Wynik (Colab, 2 vCPU):** sekwencyjnie ≈ 30.8 s, ThreadPool ≈ 31.5 s (**0.98×**), multiprocessing ≈ 30.0 s (**1.02×**). Wyniki wszystkich metod identyczne (sanity check OK).

**Insight (kluczowy):** wbrew naiwnemu oczekiwaniu **multiprocessing nie przyspieszył**. Mimo że `os.cpu_count()` zwraca 2, darmowy Colab działa w kontenerze z limitem CPU (cgroup quota) ≈ 1 rdzeń — dwa procesy konkurują o ten sam fizyczny czas CPU, więc nie ma realnej równoległości. ThreadPool jest dodatkowo wolniejszy, bo **GIL** serializuje wykonanie bajtkodu, a dochodzi narzut zarządzania wątkami. **Wniosek:** reguła „CPU-bound → multiprocessing" jest prawdziwa *warunkowo* — warunkiem jest sprzęt z wieloma niezależnymi rdzeniami. Na throttlowanym 1-rdzeniowym sandboxie żadna technika równoległości nie pomoże.

---

## Lab 3 — Testowanie (`Tokenizer` + pytest)

**Co zrobiłem:** konfigurowalny `Tokenizer` (strip HTML, lowercase, min_length, `\w+` z `re.UNICODE`) + testy w pytest: fixtury (`tokenizer`, `imdb_sample`), `parametrize` (6 przypadków brzegowych: pusty string, sam HTML, mieszany case, interpunkcja, polskie diakrytyki, zwykłe zdanie), test integracyjny na imdb i `@pytest.mark.xfail`. Testy uruchamiane przez `subprocess`.

**Wynik:** **9 passed, 1 xfailed**. Insight: 100 recenzji imdb → **5053 unikalnych tokenów**.

**Insight:** ~50 nowych unikalnych słów na recenzję to praktyczna heurystyka rozmiaru słownika (vocab rośnie sublinearnie — prawo Heapsa). `@pytest.mark.xfail` dokumentuje znane ograniczenie (brak obsługi e-maili) bez psucia zielonego builda — różnica między „testem który zawiódł" a „funkcją której świadomie nie wspieramy".

---

## Lab 4 — Bazy danych (SQL vs NoSQL-style JSON w SQLite)

**Co zrobiłem:** alternatywny schemat `reviews_json(id, doc TEXT)` z dokumentem JSON (text, label, stats, tags) + 4 zapytania `json_extract` + porównanie z klasycznym schematem relacyjnym.

**Wynik:** rozkład 1000/1000, średni word_count neg 224.7 / pos 232.2, `tags LIKE '%movie%'` = 169, top 5 najdłuższych pozytywnych (982…962 słów). Rozmiar: **SQL 3.21 MB vs JSON 3.52 MB** (~9% więcej).

**Insight:** schemat JSON jest większy, bo **każdy dokument powtarza nazwy kluczy**, a zapytania wymagają parsowania JSON-a w każdym wierszu (brak indeksu na zagnieżdżonych polach). Dla *tego* problemu (analityka po stałych wymiarach) **wygrywa klasyczny SQL**. NoSQL/JSON opłaca się przy zmiennej strukturze dokumentów lub wzorcu „czytaj/zapisuj cały dokument" (key-value), a nie przy agregacjach po pojedynczych polach — bazę dobiera się pod **wzorzec zapytań**, nie pod „jakie mam dane".

---

## Lab 5 — PySpark (window functions)

**Co zrobiłem:** ranking recenzji w obrębie klasy po długości (`row_number` nad `partitionBy("label")`), top 3 najdłuższe per klasa, różnica długości od średniej klasowej (`avg().over(window)`), oraz **moving average** długości w oknie 50 ostatnich recenzji (`rowsBetween(-49, 0)`) zwizualizowana wykresem liniowym (2 linie).

**Wynik:** top 3 najdłuższe — klasa negatywna 1020/1018/1014 słów, pozytywna 1000/998/996 słów. Średnia klasowa: neg 230.5 (zgodna z agregacją z przykładu). Różnice od średniej i krocząca średnia liczone jednym przebiegiem; wykres pokazuje stabilizację średniej długości w obu klasach.

**Insight:** window functions liczą agregat **bez kolapsu wierszy** — to czego nie da się zrobić zwykłym `groupBy` (tam tracimy poszczególne rekordy). Spark jest **leniwy**: cały łańcuch transformacji to DAG, który wykonuje się dopiero przy akcji (`show`, `toPandas`). To boli w debugowaniu — błąd w transformacji wybucha dopiero kilka linii później, przy pierwszej akcji, a nie w miejscu rzeczywistego błędu.

---

## Lab 6 — Data Quality (kontrakt + raport JSON)

**Co zrobiłem:** `DataContract` (`add_rule(name, check, severity)`) + `DataValidator` zwracający raport `{rule: {passed, severity, details}}` z **fail-fast** dla reguł `error`. 6 reguł wymaganych + bonusowa `no_html_tags` (warning). Raport zapisany do `data_quality_report.json` z timestampem.

**Wynik:** 6 reguł **PASS**, `no_html_tags` **FAIL jako warning** (walidacja nie przerywa).

**Insight:** różnica między *audytem* a *kontraktem*: audyt to analiza post-factum, kontrakt to brama wejściowa danych do pipeline'u. Severity rozróżnia „dane zepsute — stop" (`error`) od „dane nieidealne — ostrzegam" (`warning`). imdb ma dużo pozostałości HTML (`<br />`) — to nie dyskwalifikuje datasetu, ale sygnalizuje konieczność czyszczenia przed treningiem. W produkcji potrzeba **obu**: kontraktu (zapobiega wpuszczeniu złych danych) i audytu (wykrywa dryf jakości w czasie).

---

## Odpowiedzi na pytania kontrolne

1. **`functools.wraps`** — konieczny gdy zależy nam na zachowaniu metadanych funkcji (`__name__`, `__doc__`, sygnatura) — istotne dla debugowania, introspekcji, narzędzi (Sphinx, pytest). Można odpuścić tylko w jednorazowym, prywatnym kodzie.
2. **Threading vs multiprocessing** — GIL pozwala wykonywać bajtkod tylko jednemu wątkowi naraz, więc threading nie przyspiesza obliczeń (tylko I/O, gdzie wątek zwalnia GIL na czas czekania). Multiprocessing tworzy osobne interpretery (osobny GIL na proces) → realna równoległość CPU — *o ile są wolne rdzenie* (patrz Lab 2).
3. **parametrize vs osobne testy** — `parametrize` gdy ta sama logika asercji, różne dane wejściowe (zwięzłość, czytelny raport per przypadek). Osobne testy gdy różni się logika sprawdzania lub setup.
4. **schema-on-read** — strukturę nadajemy przy odczycie, nie przy zapisie. Plus: elastyczność (różne dokumenty, szybka iteracja, brak migracji). Minus: brak gwarancji integralności, wolniejsze agregacje po polach, ryzyko „śmieci" w danych.
5. **Lazy evaluation** — transformacje budują DAG, wykonują się dopiero przy akcji. Boli w debugowaniu: wyjątek pojawia się przy pierwszej akcji (`show`/`collect`), a nie w linii błędnej transformacji — stack trace wskazuje akcję, nie przyczynę.
6. **Audyt vs kontrakt** — audyt = analiza jakości po fakcie; kontrakt = walidacja na wejściu (fail-fast). W produkcji potrzeba obu: kontrakt blokuje złe dane na bramie, audyt monitoruje dryf jakości w czasie.

---

## Jak uruchomić

1. Otwórz `AAP_Zestaw_Zaliczeniowy.ipynb` w Google Colab.
2. Dodaj na górze komórkę i uruchom: `!pip install -q datasets pyspark`.
3. *Runtime → Run all*. Pierwsze uruchomienie pobiera dataset (~30 s), kolejne są błyskawiczne (cache).
4. Artefakty (bazy, raport JSON, pliki testów) powstają w `./_workspace/`.
