# CI-интеграции

[English](../INTEGRATIONS.md) | [Русский](CI_INTEGRATIONS.md) · [Индекс документации](README.md)

Команды выполняются на runner владельца репозитория. Сервис анализа, облачная база, регистрация пользователя и API DeployWitness не нужны. После установки зависимостей сам анализ не обращается к сети.

## GitHub Actions

Анализ выполняется на GitHub-hosted runner владельца репозитория. Сам workflow и исходный код анализатора должны быть закреплены за одним проверенным полным SHA DeployWitness длиной 40 символов; имена веток вроде `main` в параметре анализатора отклоняются.

Добавьте файл `.github/workflows/deploywitness.yml`:

```yaml
name: DeployWitness
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

jobs:
  compose-analysis:
    uses: Zerro15/DeployWitness/.github/workflows/deploywitness-pr.yml@REPLACE_WITH_REVIEWED_40_CHARACTER_SHA
    with:
      deploywitness_ref: REPLACE_WITH_THE_SAME_SHA
```

Перед коммитом замените оба примера одним и тем же проверенным SHA длиной 40 символов. Возьмите его из просмотренного коммита DeployWitness или опубликованного релиза. Reusable workflow отдельно получает базовую ревизию репозитория и DeployWitness, загружает head PR только как Git-данные и помещает Markdown-отчёт в summary запуска Actions. Код PR не checkout-ится и не выполняется; комментарии в PR и передача конфигурации на сервер DeployWitness не используются. Зависимости GitHub Actions в workflow также закреплены полными SHA.

Вызывающему workflow достаточно `contents: read`. Он запускается на событии `pull_request`, поэтому PR из fork использует read-only token GitHub без секретов; настоящий запуск для fork в этой alpha пока не проверен. GitHub может потребовать одобрить запуск workflow от нового участника.

После установки откройте PR с изменением поддерживаемого файла Compose (`compose.yaml`, `compose.yml`, `docker-compose.yaml` или `docker-compose.yml`) и проверьте запуск в Actions. Для безопасной правки ожидается `NO_FINDING`; удаление связи без явного контракта даёт только предупреждение; неподдерживаемый или неполный вход даёт `UNKNOWN` и завершает проверку ошибкой. Полная таблица входов — в разделе [поддерживаемых возможностей Compose](SUPPORTED_COMPOSE_FEATURES.md).

### Где найти отчёт

Откройте вкладку репозитория **Actions**, выберите запуск **DeployWitness**, связанный с нужным PR, и прочитайте **сводку запуска workflow (workflow run summary)**. Markdown-отчёт находится в сводке задания. Откройте само задание, если нужны логи шагов. DeployWitness не публикует комментарий в PR.

`PROVEN_CONFIG_BREAK` завершает проверку ошибкой. `POTENTIAL_RISK` остаётся предупреждением. `UNKNOWN` явно обозначает неполный анализ и также завершает проверку ошибкой. Чистый результат означает только отсутствие проблем среди реализованных правил. Добавленные или удалённые Compose-файлы, несколько Compose-файлов в одной директории, изменённый `.env` или другой соседний YAML, неподдерживаемые возможности и слишком большие файлы дают `UNKNOWN`.

[Ручной пример workflow](../../.github/workflows/example-check.yml) по-прежнему доступен для запуска CLI на фиксированных примерах репозитория.

## GitLab CI

Пример из [`docs/INTEGRATIONS.md`](../INTEGRATIONS.md) показывает вызов CLI для файлов репозитория. Чтобы проверять изменения merge request, runner должен безопасно подготовить базовый и кандидатный YAML и передать их через `--base` и `--head`. Автоматическая подготовка в примере не реализована.

```yaml
deploywitness:
  image: python:3.12
  script:
    - pip install .
    - deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

## Forgejo Actions

Пример использует runner Forgejo и сравнивает указанные файлы. Автоматическое получение ревизий PR или комментарии в PR не реализованы.

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install .
      - run: deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

## Выбор входов

Каждый вызов `check` принимает ровно один базовый и один кандидатный Compose-файл. Compose overrides не объединяются. Передавайте проверенные эффективные файлы; не запускайте команды или код из недоверенного PR. См. [справочник CLI](CLI_REFERENCE.md) и [безопасность](SECURITY.md).
