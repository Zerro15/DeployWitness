<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/wordmark-dark.svg">
    <img src="assets/brand/wordmark-light.svg" alt="DeployWitness" width="520">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> | <a href="README.ru.md">Русский</a></p>
<p align="center"><strong>Know what breaks before you deploy.</strong><br>
Сравнивайте конфигурации Docker Compose и проверяйте контракты, чтобы понимать, какое изменение действительно нарушает заданный инвариант.</p>

<p align="center">
  <a href="docs/ru/GETTING_STARTED.md">Начало работы</a> ·
  <a href="docs/ru/FAILURE_WITNESS.md">Как читать доказательство</a> ·
  <a href="docs/ru/README.md">Вся документация</a> ·
  <a href="CONTRIBUTING.md">Участие в проекте</a>
</p>

---

## Проблема

Изменение Compose может удалить сервис, разорвать сетевую связь между сервисами или заменить подключение постоянного хранилища. Линтер замечает подозрительный фрагмент, но обычно не сравнивает прежние и новые связи и не показывает, какой именно объявленный инвариант нарушен.

DeployWitness сравнивает две конфигурации. Статус **доказанного нарушения конфигурационного контракта** появляется только тогда, когда проверяемый инвариант выполнялся в базовой конфигурации и перестал выполняться в новой. Если изменение выглядит значимым, но контракта недостаточно, это **риск**, а не доказанная авария.

## Пример работы

В исходной конфигурации объявлено, что `api` и `db` должны находиться в общей сети. Новая версия переносит `api` в другую сеть. Исправленный вариант возвращает требуемую связь.

![Сетевая связь Compose до изменения, после него и после исправления](assets/readme/before-after.svg)

Запустите из корня репозитория:

```console
$ deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
PROVEN_CONFIG_BREAK COMPOSE_NETWORK_LINK api->db: Required or previously shared service network is absent
  Fix: Attach api and db to one shared network, or update the contract deliberately
```

Результат доказывает статическое нарушение контракта Compose. Он не означает, что запрос в работающем сервисе завершился ошибкой. Для исправленной конфигурации эта проверка возвращает `NO_FINDING` только по реализованным правилам; это не гарантия безопасности.

## Возможности

| | Что означает сейчас |
| --- | --- |
| **Сравнение конфигураций** | Сопоставляет сервисы, сети, зависимости, подключения томов и ключи окружения в двух Compose-файлах. |
| **Детерминированное свидетельство** | Повторно вычисляет результат из исходных файлов; статическая проверка сверяет все существенные поля свидетельства. |
| **Уровни уверенности** | Разделяет `PROVEN_CONFIG_BREAK`, `POTENTIAL_RISK` и `UNKNOWN`. `REPRODUCED_FAILURE` зарезервирован для будущих runtime-тестов и сейчас не выдаётся. |
| **Локальная работа** | Для анализа не нужны учётная запись, сервер, телеметрия, Docker daemon или socket. |
| **Ваши вычислительные ресурсы** | Запускайте CLI на своём компьютере или CI runner. Проект не получает ваши конфигурации. |
| **Честное покрытие** | Неподдерживаемые или неразрешённые особенности Compose отражаются как `UNKNOWN`, а не как подтверждение безопасности. |

## Быстрый запуск

Нужен Python 3.12 или новее. Пакет пока не опубликован в PyPI. Чтобы попробовать текущую Compose alpha, установите пакет из её ветки:

```bash
git clone --branch feat/compose-witness-mvp https://github.com/Zerro15/DeployWitness.git
cd DeployWitness
python -m pip install .
deploywitness check --base examples/before/compose.yaml --head examples/after/compose.yaml
```

`scan` находит Compose-файл и показывает количество сервисов, но **не сравнивает изменения**. Для сравнения нужны явные файлы `--base` и `--head`. Если обнаружено несколько стандартных имён, выберите файл через `--file`: инструмент не угадывает, какой конфигурации соответствует production.

```bash
deploywitness scan .
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format markdown
deploywitness check --base ./before/compose.yaml --head ./after/compose.yaml --format json
deploywitness rules
deploywitness version
```

Коды завершения: `0` — доказанного нарушения нет (риски возможны); `2` — найдено хотя бы одно доказанное нарушение контракта; `3` — некорректный или неразрешённый ввод.

## Как устроен анализ

![Поток локального анализа DeployWitness](assets/readme/architecture.svg)

Парсер читает ограниченное безопасное подмножество YAML: он не выполняет команды Compose и не подставляет секреты. Движок сравнивает факты и явно заданные контракты, затем формирует структурированное свидетельство. Отчёт создаётся локально в форматах terminal, JSON или Markdown.

### Поддержка и ограничения alpha

Сейчас поддерживается один эффективный Compose-файл на каждую сторону сравнения. Ациклические YAML anchors и aliases, а также имена объявленных external networks распознаются; существование внешней сети инструмент не проверяет. Profiles, interpolation, `include`, `extends`, `network_mode`, YAML merge keys и объединение override-файлов не поддерживаются и дают `UNKNOWN` или неполный результат. Перед интерпретацией чистого отчёта прочитайте [список возможностей и ограничений](docs/ru/SUPPORTED_COMPOSE_FEATURES.md).

Контракты задаются расширением `x-deploywitness`. Например, можно явно потребовать общую сеть между сервисами:

```yaml
x-deploywitness:
  required_network_links:
    - from: api
      to: db
```

Без такого контракта удаление связи считается риском. Один лишь `depends_on` не доказывает необходимость сетевого соединения. Контракт `required_mounts` проверяет наличие точки монтирования; изменение источника — это риск, а не доказательство потери данных. Значения переменных окружения и их хеши не попадают в отчёты.

## CI-интеграции

В репозитории есть [пример GitHub Actions](.github/workflows/example-check.yml), который запускается на runner владельца репозитория с правом `contents: read`. Текущие примеры GitHub, GitLab и Forgejo сравнивают явно заданные файлы. **Автоматическое получение base/head для PR и опубликованного GitHub Action пока нет.** См. [примеры интеграций](docs/ru/CI_INTEGRATIONS.md).

## Документация

- [Начало работы](docs/ru/GETTING_STARTED.md) · [Справочник CLI](docs/ru/CLI_REFERENCE.md)
- [Failure Witness](docs/ru/FAILURE_WITNESS.md) · [Поддерживаемые возможности Compose](docs/ru/SUPPORTED_COMPOSE_FEATURES.md)
- [Архитектура](docs/ru/ARCHITECTURE.md) · [Безопасность](docs/ru/SECURITY.md)
- [CI-интеграции](docs/ru/CI_INTEGRATIONS.md) · [FAQ](docs/ru/FAQ.md)
- [Индекс документации](docs/ru/README.md) · [Руководство по переводам](docs/i18n/TRANSLATION_GUIDE.md)

## Дорожная карта

Текущая alpha реализует только часть статического MVP для Compose. В ближайших приоритетах — более точная обработка семантики Compose, расширение набора проверок на ложные срабатывания и пропуски, сравнение Git-ревизий и проверенные CI-сценарии. Полный план и критерии готовности указаны в [ROADMAP.md](ROADMAP.md); запланированные возможности не следует считать уже выпущенными.

## Участие в проекте

Читайте [CONTRIBUTING.md](CONTRIBUTING.md). Ошибки, предложения и вопросы можно писать на русском или английском. Для технических изменений приложите минимальную пару Compose-файлов и ожидаемый результат. Не отправляйте реальные секреты и конфигурации заказчиков.

```bash
python -m pytest
python -m ruff check .
python -m mypy src
python -m build
git diff --check
```

DeployWitness распространяется по лицензии Apache-2.0. См. [LICENSE](LICENSE).
