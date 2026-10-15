# CI-интеграции

[English](../INTEGRATIONS.md) | [Русский](CI_INTEGRATIONS.md) · [Индекс документации](README.md)

Команды выполняются на runner владельца репозитория. Сервис анализа, облачная база, регистрация пользователя и API DeployWitness не нужны. После установки зависимостей сам анализ не обращается к сети.

## GitHub Actions

DeployWitness предоставляет reusable workflow, который сравнивает base и head PR на GitHub-hosted runner владельца репозитория. Добавьте workflow:

```yaml
name: DeployWitness
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

jobs:
  compose-analysis:
    uses: Zerro15/DeployWitness/.github/workflows/deploywitness-pr.yml@main
    with:
      deploywitness_ref: main
```

Для постоянного использования замените оба значения `@main` и `deploywitness_ref: main` одним и тем же проверенным SHA DeployWitness. Workflow отдельно получает базовую ревизию репозитория и исходный код DeployWitness, загружает head PR только как Git-данные и помещает Markdown-отчёт в summary запуска Actions. Код PR не checkout-ится и не выполняется; комментарии в PR и передача конфигурации на сервер DeployWitness не используются.

### Где найти отчёт

Откройте вкладку репозитория **Actions**, выберите запуск **DeployWitness**, связанный с нужным PR, и прочитайте **сводку запуска workflow (workflow run summary)**. Markdown-отчёт находится в сводке задания. Откройте само задание, если нужны логи шагов. DeployWitness не публикует комментарий в PR.

PROVEN_CONFIG_BREAK завершает проверку ошибкой. POTENTIAL_RISK остаётся предупреждением. UNKNOWN явно обозначает неполный анализ и также завершает проверку ошибкой. Чистый результат означает только отсутствие проблем среди реализованных правил. Добавленные или удалённые Compose-файлы, несколько Compose-файлов в одной директории, неподдерживаемые возможности и слишком большие файлы дают UNKNOWN.

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
