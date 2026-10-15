# Начало работы

[English](../GETTING_STARTED.md) | [Русский](GETTING_STARTED.md) · [Индекс документации](README.md)

## Требования

- Python 3.12 или новее.
- Проверенный YAML-файл Docker Compose. Docker Engine и Docker CLI для статического анализа не нужны.
- Для установки Python-зависимостей нужен доступ к сети, если они ещё не установлены. После установки сам анализ не обращается к сети.

## Установка проверенного commit main до релиза

До публикации первого релиза установите проверенный commit `main` `f40f05da1a374a79979d8958e8bacef7c360848b`:

```bash
git clone https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
git checkout --detach f40f05da1a374a79979d8958e8bacef7c360848b
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

Пример выдаёт `PROVEN_CONFIG_BREAK`, потому что в базовой конфигурации явно требуется общая сеть, а в кандидате эта связь удалена. Это доказывает статическое нарушение конфигурационного контракта, но не аварию во время работы.

## Установка из GitHub Release

После публикации `v0.1.0a1` рекомендуется установить wheel из [GitHub Release](https://github.com/Zerro15/DeployWitness/releases). Скачайте `deploywitness-0.1.0a1-py3-none-any.whl` и `SHA256SUMS.txt` в одну папку. Проверьте wheel этой командой стандартной библиотеки Python: она сверяет только указанный wheel, поэтому sdist скачивать не нужно.

```text
python -c "import hashlib,pathlib,sys; f='deploywitness-0.1.0a1-py3-none-any.whl'; sums={name:digest for digest,name in (line.split(maxsplit=1) for line in pathlib.Path('SHA256SUMS.txt').read_text(encoding='ascii').splitlines())}; actual=hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest(); print('SHA256 OK:', f) if sums.get(f)==actual else sys.exit('SHA256 verification failed')"
```

Одна и та же команда работает в Linux, macOS и Windows PowerShell. Затем установите пакет и проверьте его:

```text
python -m pip install ./deploywitness-0.1.0a1-py3-none-any.whl
deploywitness version
```

Для окружений, которым wheel не подходит, будет также приложен исходный архив `.tar.gz`; чтобы проверить его, замените имя файла в команде на `deploywitness-0.1.0a1.tar.gz`. Для установки зависимостей может потребоваться доступ к настроенному Python package index. Сам анализ сетевых запросов не выполняет. Файлы появятся только после публикации GitHub pre-release. Настоящий запуск GitHub PR из fork пока не проверен; см. [ограничения интеграции](../INTEGRATIONS.md).

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
