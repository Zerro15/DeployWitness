# Начало работы

[English](../GETTING_STARTED.md) | [Русский](GETTING_STARTED.md) · [Индекс документации](README.md)

## Требования

- Python 3.12 или новее.
- Проверенный YAML-файл Docker Compose. Docker Engine и Docker CLI для статического анализа не нужны.
- Для установки Python-зависимостей нужен доступ к сети, если они ещё не установлены. После установки сам анализ не обращается к сети.

## Попробовать текущую alpha

Пакет пока не опубликован в PyPI, а в `main` ещё нет устанавливаемого пакета. Текущий CLI находится в [Draft PR #1](https://github.com/Zerro15/DeployWitness/pull/1). Установите пакет из его ветки:

```bash
git clone --branch feat/compose-witness-mvp https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

Пример выдаёт `PROVEN_CONFIG_BREAK`, потому что в базовой конфигурации явно требуется общая сеть, а в кандидате эта связь удалена. Это доказывает статическое нарушение конфигурационного контракта, но не аварию во время работы.

## Просканировать одну конфигурацию

```bash
deploywitness scan .
```

`scan` находит один файл со стандартным именем Compose и показывает количество разобранных сервисов. Команда **не сравнивает изменения** и не подтверждает безопасность. Если найдено несколько стандартных файлов, укажите конкретный проверенный файл через `--file`. Для анализа изменений используйте `check` с обеими версиями.

## Сравнить изменения

```bash
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format markdown
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format json
```

С каждой стороны сравнения разбирается один файл. Compose overrides не объединяются. Подготовьте и проверьте эффективные файлы заранее; не запускайте интерполяцию Compose или команды из недоверенного репозитория для подготовки входных данных.

## Локальная разработка

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
python -m build
```

Подробнее: [справочник CLI](CLI_REFERENCE.md), [поддерживаемые возможности](SUPPORTED_COMPOSE_FEATURES.md), [безопасность](SECURITY.md).
