# CI-интеграции

[English](../INTEGRATIONS.md) | [Русский](CI_INTEGRATIONS.md) · [Индекс документации](README.md)

Команды выполняются на runner владельца репозитория. Сервис анализа, облачная база, регистрация пользователя и API DeployWitness не нужны. После установки зависимостей сам анализ не обращается к сети.

## GitHub Actions

В репозитории есть [пример workflow](../../.github/workflows/example-check.yml). Он запускается вручную (`workflow_dispatch`), имеет `contents: read` и сравнивает фиксированные файлы `examples/before/compose.yaml` и `examples/fixed/compose.yaml`.

Это демонстрация запуска CLI, а не готовая проверка Pull Request: workflow не получает base/head PR автоматически, не создаёт комментарий или Markdown summary и не использует отдельный GitHub Action. Не применяйте привилегированный `pull_request_target` для запуска недоверенного кода.

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
