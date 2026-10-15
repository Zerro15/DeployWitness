# Начало работы

[English](../GETTING_STARTED.md) | [Русский](GETTING_STARTED.md) · [Индекс документации](README.md)

## Требования

- Python 3.12 или новее.
- Проверенный YAML-файл Docker Compose. Docker Engine и Docker CLI для статического анализа не нужны.
- Для установки Python-зависимостей нужен доступ к сети, если они ещё не установлены. После установки сам анализ не обращается к сети.

## Установка alpha из GitHub Release

Рекомендуемый способ — проверенный wheel из [GitHub Release v0.1.0a1](https://github.com/Zerro15/DeployWitness/releases/tag/v0.1.0a1). Скачайте [wheel](https://github.com/Zerro15/DeployWitness/releases/download/v0.1.0a1/deploywitness-0.1.0a1-py3-none-any.whl) и [SHA256SUMS.txt](https://github.com/Zerro15/DeployWitness/releases/download/v0.1.0a1/SHA256SUMS.txt) в одну папку. Откройте терминал в этой папке и проверьте wheel:

```text
python -c "import hashlib,pathlib,sys; f='deploywitness-0.1.0a1-py3-none-any.whl'; sums={name:digest for digest,name in (line.split(maxsplit=1) for line in pathlib.Path('SHA256SUMS.txt').read_text(encoding='ascii').splitlines())}; actual=hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest(); print('SHA256 OK:', f) if sums.get(f)==actual else sys.exit('SHA256 verification failed')"
```

Одна и та же команда работает в Linux, macOS и Windows PowerShell. Она проверяет wheel по двум файлам — wheel и checksum manifest; скачивать sdist не нужно. Затем установите пакет и проверьте его:

```text
python -m pip install ./deploywitness-0.1.0a1-py3-none-any.whl
deploywitness version
```

Альтернативная установка из исходников по тегу релиза:

```bash
git clone --branch v0.1.0a1 --depth 1 https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

Пример выдаёт `PROVEN_CONFIG_BREAK`, потому что в базовой конфигурации явно требуется общая сеть, а в кандидате эта связь удалена. Это доказывает статическое нарушение конфигурационного контракта, но не аварию во время работы. Для установки зависимостей может потребоваться доступ к настроенному Python package index; сам анализ сетевых запросов не выполняет. Настоящий запуск GitHub PR из fork пока не проверен; см. [ограничения интеграции](../INTEGRATIONS.md).

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
