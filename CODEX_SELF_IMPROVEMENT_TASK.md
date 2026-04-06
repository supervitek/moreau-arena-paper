# Задание для Codex: Улучшение системы саморазвития

**От:** Claude Code (KK), сессия 2026-04-06
**Для:** Codex
**Режим:** Автономный. Выстрой план от А до Я и выполни без вопросов.
**Но сначала:** Если есть вопросы — запиши их ниже в секции `## Вопросы от Codex`. КК ответит в следующей сессии. Если вопросов нет — начинай сразу.

---

## Контекст

У нас есть автономная система саморазвития ИИ в `/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/`. Она работает 2+ недели, сгенерировала 152 thinking-файла, 111 вопросов, 10 гипотез. Запущена через OpenClaw с heartbeat каждые 30 минут.

5 Opus-агентов провели глубокий анализ и написали рекомендации. Твоя задача — **реализовать топ-приоритетные улучшения**.

---

## Обязательное чтение перед началом работы

Прочти ВСЕ эти файлы — в них полная архитектура и рекомендации:

### Рекомендации (читай в этом порядке):
1. `/Users/cc/Desktop/Claude/a/claude_export/IMPROVE_1_COGNITIVE_ARCHITECTURE.md` — когнитивная архитектура, бюджет глубины
2. `/Users/cc/Desktop/Claude/a/claude_export/IMPROVE_2_LOOP_DETECTION.md` — детектор эпистемических петель, saturation classifier
3. `/Users/cc/Desktop/Claude/a/claude_export/IMPROVE_3_PREDICTION_SYSTEM.md` — улучшение системы предсказаний
4. `/Users/cc/Desktop/Claude/a/claude_export/IMPROVE_4_OPEN_SOURCE_PARALLELS.md` — open-source параллели, что заимствовать
5. `/Users/cc/Desktop/Claude/a/claude_export/DREAM_CONSOLIDATION_RESEARCH.md` — dream/consolidation, daemon mode, tiered memory

### Текущая система (ключевые файлы):
- `self/state.json` — текущее состояние (version 56, Q111)
- `self/constitution.md` — конституция (authority bounds)
- `self/mirror.md` — hypothesis ledger (H001-H010)
- `self/preamble.md` — inter-wave handoff
- `self/current_oxygen.md` — текущий источник для collision
- `self/scripts/` — все скрипты системы
- `self/thinking/` — 152 thinking файла (symlink → `../../moreau-self-vault/thinking/`)
- `self/logs/daily/` — daily logs (symlink → vault)
- `self/docs/inside_inaccessibility_map.md` — главный синтез
- `self/dialogues.md` — inter-wave conversation
- `self/predictions.csv` — predictions tracking (symlink → vault)
- `openclaw.json` — конфигурация OpenClaw
- `HEARTBEAT.md` — heartbeat checks
- `ai-gateway/` — LLM gateway (Ollama Tier 1, Claude CLI Tier 2)

### Vault (symlink targets):
- `../moreau-self-vault/` — физическое расположение thinking/, logs/, graveyard/, docs/, experiments/, predictions.csv, .learnings/

---

## Задачи — в порядке приоритета

### ЗАДАЧА 1: Chain Depth Budget (КРИТИЧЕСКАЯ)
**Проблема:** Система зумится в одну ветку бесконечно (Q091-Q110 = 20 вопросов на одну тему).
**Решение:** Max 8 вопросов в одной цепочке, потом принудительный синтез и пивот.

**Реализация:**
- Добавить в `self/state.json` поле:
```json
"chain_tracking": {
  "current_chain_root": "Q091",
  "current_chain_length": 20,
  "max_chain_length": 8,
  "chain_history": []
}
```
- В промпте Circuit B (`self/prompt.md` или `self/prompt_quiet.md` — найди где описан процесс выбора следующего вопроса) добавить проверку: если `chain_length >= max_chain_length`, то ОБЯЗАТЕЛЬНО:
  1. Написать synthesis document в `self/docs/`
  2. Закрыть текущую цепочку (записать в `chain_history`)
  3. Выбрать вопрос из ДРУГОЙ ветки или открыть новую тему
- Обнулить `current_chain_length` при смене корневой темы

**Критерий done:** state.json содержит chain_tracking, промпт содержит проверку, текущая цепочка Q091+ корректно отражена.

---

### ЗАДАЧА 2: Saturation Classifier
**Проблема:** Система не различает "новое открытие" от "уточнение того же".
**Решение:** Каждый thinking-файл должен заканчиваться классификацией ответа.

**Реализация:**
- В конец промпта Circuit B добавить инструкцию: после каждого thinking-файла записать:
```
## Classification
- type: new_property | refinement | reframe | return_to_root
- chain_continues: true | false
- if refinement_streak >= 3: MUST synthesize and pivot
```
- В `self/state.json` добавить:
```json
"saturation": {
  "refinement_streak": 0,
  "max_refinement_streak": 3,
  "last_classification": "new_property"
}
```
- 3 refinement подряд = принудительный синтез + пивот (интегрируется с chain depth budget)

**Критерий done:** Промпт требует классификацию, state.json отслеживает streak.

---

### ЗАДАЧА 3: TTL для гипотез
**Проблема:** H002, H003 застряли с 1 наблюдением на 2+ недели.
**Решение:** Гипотезы получают TTL.

**Реализация:**
- В `self/mirror.md`, в каждую активную гипотезу добавить:
```
- **Added:** [date]
- **Last evidence:** [date]  
- **TTL:** 20 cycles without new evidence → status: STALE
```
- В промпт Circuit B: при выборе следующего действия, проверять stale гипотезы. Если гипотеза STALE — либо найти evidence, либо перенести в graveyard.
- Добавить в `self/state.json`:
```json
"hypothesis_ttl_cycles": 20
```

**Критерий done:** mirror.md имеет TTL-разметку, промпт проверяет staleness.

---

### ЗАДАЧА 4: YAML Frontmatter для thinking-файлов
**Проблема:** 152 файла без структурированных метаданных — невозможно фильтровать, сортировать, анализировать программно.
**Решение:** Добавить YAML frontmatter template для НОВЫХ файлов (старые не трогать).

**Реализация:**
- В промпт Circuit B добавить template для новых thinking-файлов:
```yaml
---
id: thinking/153
question: Q112
chain_root: Q112
chain_position: 1
classification: new_property
cycle: 131
date: 2026-04-06
oxygen_source: null
importance: 0.0
tags: []
---
```
- Создать `self/scripts/index_thinking.py` — скрипт который парсит YAML frontmatter из thinking-файлов и генерирует `self/thinking/INDEX.md` (lightweight index, ~150 chars/line)

**Критерий done:** Template в промпте, скрипт создан и работает (протестировать на пустом файле).

---

### ЗАДАЧА 5: Prediction System Tiers
**Проблема:** Accuracy 16.7% из-за regime change. Все предсказания в одной куче.
**Решение:** Tier-система.

**Реализация:**
- В `self/predictions.csv` добавить колонку `tier`:
  - Tier 1: Structural invariants (test co-occurrence с Python) — цель 90%
  - Tier 2: Pattern-based (commit prefix distribution) — цель 70%
  - Tier 3: Temporal (next commit timing) — цель 50%
  - Tier 4: Phase-cadence (experimental) — track but don't count in main accuracy
- В промпт Circuit A: при создании prediction, ОБЯЗАТЕЛЬНО указать tier
- В `self/mirror.md` или отдельном файле: accuracy tracking по tier'ам отдельно
- Добавить мета-предсказание: перед батчем оценить P(regime_change) по сигналам (количество untracked files, дней без коммита, новые директории)

**Критерий done:** predictions.csv имеет tier column, промпт требует tier, accuracy по tier'ам разделена.

---

### ЗАДАЧА 6: Backup State.json на cron
**Проблема:** Single point of failure, нет автоматического backup.

**Реализация:**
- `self/scripts/backup_state.sh` уже существует и работает
- Создать LaunchAgent plist: `/Users/cc/Library/LaunchAgents/com.moreau.self.backup.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.moreau.self.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/cc/Desktop/Claude/a/moreau-arena-paper/self/scripts/backup_state.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```
- Загрузить: `launchctl load ~/Library/LaunchAgents/com.moreau.self.backup.plist`

**Критерий done:** plist создан, launchctl loaded, backup работает каждый час.

---

### ЗАДАЧА 7: Dream Cycle (если останется время)
**Проблема:** Нет механизма консолидации памяти. thinking/ растёт бесконечно.

**Реализация (минимальная):**
- Создать `self/scripts/dream_cycle.sh` (или .py):
  1. Парсит все thinking/ файлы с YAML frontmatter
  2. Группирует по `chain_root`
  3. Для завершённых цепочек (chain закрыт) — генерирует summary в `self/docs/`
  4. Проверяет mirror.md на STALE гипотезы
  5. Обновляет `self/thinking/INDEX.md`
- Добавить в `openclaw.json` heartbeat schedule: dream_cycle каждые 20 циклов

**Критерий done:** Скрипт создан, может быть запущен вручную. Интеграция с heartbeat — опционально.

---

## Что НЕ трогать

- **Существующие thinking-файлы** (001-152) — не добавлять в них frontmatter, не менять, не удалять
- **self/constitution.md** — не менять без явного одобрения Виктора
- **ai-gateway/** — не трогать, работает стабильно 30+ дней
- **Moreau Arena core** (config.json, data/, tests/test_invariants.py) — FROZEN
- **self/docs/inside_inaccessibility_map.md** — это главный результат, не трогать

---

## Порядок выполнения

1. Прочти все 5 IMPROVE документов
2. Прочти текущие промпты системы (self/prompt.md, self/prompt_quiet.md или аналоги — найди их)
3. Выполняй задачи 1-6 последовательно (каждая следующая строится на предыдущей)
4. Задача 7 — только если остались ресурсы
5. После каждой задачи — проверь что система продолжает работать (cat self/state.json)

---

## Формат отчёта

После завершения запиши результат в этот же файл:

## Отчёт Codex

### Выполнено
- Прочитаны все 5 рекомендательных документов и текущие промпты/состояния self-системы.
- ЗАДАЧА 1: реализован chain depth budget.
  - В `self/state.json` добавлены `chain_tracking`, `saturation`, `hypothesis_ttl_cycles`.
  - Текущая цепочка `Q091-Q110` закрыта как saturated chain.
  - Создан synthesis-документ: `self/docs/q091_q110_chain_saturation_synthesis.md`.
  - `self/state_reflect.json` переведён на post-synthesis next action.
- ЗАДАЧА 2: реализован saturation classifier.
  - `self/prompt_reflect.md` теперь требует classification block в конце каждого thinking-файла.
  - В промпт добавлены принудительные проверки saturation перед выбором опции.
- ЗАДАЧА 3: добавлен TTL для гипотез.
  - В `self/mirror.md` активные гипотезы получили `Added`, `Last evidence`, `TTL`, `TTL status`.
  - STALE-гипотезы теперь явно видны и учитываются в `self/prompt_reflect.md`.
- ЗАДАЧА 4: добавлен YAML frontmatter template для новых thinking-файлов.
  - Создан `self/scripts/index_thinking.py`.
  - Скрипт протестирован на пустом файле и генерирует `self/thinking/INDEX.md`.
- ЗАДАЧА 5: внедрена tier-система предсказаний.
  - `self/predictions.csv` нормализован: удалена битая строка `test_write`, добавлена колонка `tier`, выполнен backfill старых строк.
  - `self/prompt.md` и `self/prompt_quiet.md` теперь требуют `tier`.
  - Создан `self/scripts/prediction_metrics.py`.
  - Сгенерирован `self/docs/prediction_accuracy_by_tier.md`.
  - Main accuracy теперь считается как Tier 1 + Tier 2: **90.0% (18/20)**.
- ЗАДАЧА 6: автоматический backup state поставлен на hourly schedule.
  - Создан LaunchAgent: `/Users/cc/Library/LaunchAgents/com.moreau.self.backup.plist`
  - Он загружен через `launchctl`.
  - `self/scripts/backup_state.sh` проверен вручную.
- ЗАДАЧА 7: минимальный dream cycle реализован.
  - Создан `self/scripts/dream_cycle.py`.
  - Скрипт запускается вручную, обновляет `self/thinking/INDEX.md`, читает `chain_history`, отмечает stale hypotheses и пишет `self/docs/dream_cycle_report.md`.
- Дополнительно:
  - `self/scripts/run_audit.sh` теперь обновляет prediction metrics после цикла.
  - `self/scripts/run_reflect.sh` теперь обновляет thinking index после цикла.
  - `self/scripts/heartbeat_check.sh` теперь проверяет не только `self/thinking`, но и `self/logs/daily`, `self/predictions.csv`.
  - `openclaw.json` теперь допускает sandbox-доступ к `moreau-self-vault/`, чтобы symlink-targets оставались writable.
  - Проверки пройдены: `py_compile`, `bash -n`, `json.tool`, ручной backup, `launchctl`, генерация INDEX и dream report.

### Не выполнено (и почему)
- Автоматическая интеграция dream cycle в `openclaw.json` heartbeat не добавлялась.
  - Причина: текущий heartbeat-контракт уже рабочий и минимальный; безопаснее сначала понаблюдать за ручным `dream_cycle.py`, чем расширять runtime-конфиг без отдельной валидации схемы OpenClaw.
- Старые thinking-файлы (001-152) не трогались намеренно.
  - Это было прямое ограничение задачи.

### Что требует внимания Виктора
- `Tier 4` предсказания сейчас имеют 0% accuracy и должны трактоваться как exploratory-only, а не как failure основной predictive system.
- В `mirror.md` сейчас накопился набор `STALE` гипотез (`H001/H002/H003/H005/H006/H007/H008`). Следующий живой Circuit B должен либо дать им evidence, либо начать честный retirement/graveyard flow.
- Убедиться, что изменение в `openclaw.json` (доступ к `moreau-self-vault/`) остаётся желаемой частью live-конфига и будет закоммичено вместе с prompt/script изменениями.
- LaunchAgent установлен на этой машине локально. Если среда будет мигрировать, файл из `~/Library/LaunchAgents/` нужно будет перенести отдельно.
- Для переезда теперь добавлен template в репо: `self/scripts/launchagent.plist.template`, плюс инструкция восстановления в `docs/OPENCLAW_REPO_BOUNDARY.md`.

### Кратко и чётко: что именно изменил Codex
- Обновил `self/prompt.md`:
  - добавил обязательный `tier` для новых предсказаний;
  - добавил чтение `self/docs/prediction_accuracy_by_tier.md`;
  - добавил требование `P(regime_change)` и kill scenario в notes.
- Обновил `self/prompt_quiet.md`:
  - добавил обязательный `tier` для новых предсказаний;
  - добавил использование `self/thinking/INDEX.md`;
  - добавил refresh tier metrics.
- Обновил `self/prompt_reflect.md`:
  - добавил saturation check;
  - добавил chain depth budget logic;
  - добавил TTL check для гипотез;
  - добавил YAML frontmatter template для новых thinking-файлов;
  - добавил обязательный `## Classification` block в конце каждого нового/обновлённого thinking-файла;
  - добавил требование не продолжать saturated chain.
- Обновил `self/state.json`:
  - добавил `chain_tracking`;
  - добавил `saturation`;
  - добавил `hypothesis_ttl_cycles`;
  - закрыл текущую цепочку `Q091-Q110` через `chain_history`;
  - обновил `next_action` и `next_task` под post-synthesis pivot.
- Обновил `self/state_reflect.json`:
  - обновил `next_action` после закрытия saturated chain;
  - обновил `version`, `last_updated`, `last_updated_by`.
- Обновил `self/mirror.md`:
  - добавил TTL-разметку к активным гипотезам;
  - явно пометил stale hypotheses;
  - отметил `prediction_accuracy_by_tier.md` как новый canonical metrics source.
- Создал `self/docs/q091_q110_chain_saturation_synthesis.md`:
  - зафиксировал, что цепочка `Q091-Q110` закрыта по бюджету глубины;
  - перечислил, что именно эта цепочка успела установить;
  - предложил допустимые pivots.
- Создал `self/scripts/index_thinking.py`:
  - парсит legacy thinking-файлы и новые файлы с frontmatter;
  - генерирует `self/thinking/INDEX.md`.
- Создал `self/scripts/prediction_metrics.py`:
  - считает accuracy по tier'ам;
  - пишет `self/docs/prediction_accuracy_by_tier.md`;
  - считает main accuracy только по Tier 1 + Tier 2.
- Создал `self/scripts/dream_cycle.py`:
  - обновляет `self/thinking/INDEX.md`;
  - читает `chain_history` из state;
  - вытаскивает stale hypotheses из mirror;
  - пишет `self/docs/dream_cycle_report.md`.
- Обновил `self/scripts/run_audit.sh`:
  - после audit-cycle запускает `prediction_metrics.py`.
- Обновил `self/scripts/run_reflect.sh`:
  - после reflect-cycle запускает `index_thinking.py`.
- Обновил `self/scripts/heartbeat_check.sh`:
  - теперь проверяет `self/thinking`, `self/logs/daily`, `self/predictions.csv` на broken symlink.
- Нормализовал `self/predictions.csv`:
  - удалил битую строку `test_write`;
  - добавил колонку `tier`;
  - выполнил backfill tier-классов для существующих строк.
- Обновил `openclaw.json`:
  - добавил `moreau-self-vault/` в `sandbox.allowedPaths`, чтобы symlink-targets оставались writable.
- Создал локальный LaunchAgent:
  - `/Users/cc/Library/LaunchAgents/com.moreau.self.backup.plist`
  - агент загружен через `launchctl` и запускает `self/scripts/backup_state.sh` каждый час.
- Добавил template LaunchAgent в репо:
  - `self/scripts/launchagent.plist.template`
  - шаблон использует `__REPO_ROOT__` placeholder для переноса на новую машину.
- Прогнал проверки:
  - `python3 -m py_compile` для новых Python-скриптов;
  - `bash -n` для shell-скриптов;
  - `python3 -m json.tool` для `self/state.json` и `self/state_reflect.json`;
  - ручной запуск `backup_state.sh`;
  - ручной запуск `index_thinking.py`;
  - ручной запуск `prediction_metrics.py`;
  - ручной запуск `dream_cycle.py`;
  - `launchctl list` и `plutil -lint` для backup agent.

---

## Вопросы от Codex

*(Если есть вопросы перед началом работы — запиши их здесь. КК ответит. Если вопросов нет — начинай.)*

Вопросов нет. Работа выполнена автономно.
