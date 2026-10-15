# Contributing

Open an issue describing the problem and an example Compose pair. You may report bugs, suggest features, and ask questions in English or Russian. Public issue and pull request titles should preferably be in English so contributors can find them internationally.

For code changes, use a feature branch, add a regression case when behavior changes, and run `python -m pytest`, `python -m ruff check .`, `python -m mypy src`, and `python -m build`. Do not include real credentials or customer configurations. Keep findings conservative: prove only explicit, statically checkable invariants.

Translations are welcome. English documentation is the source of truth; see [the translation guide](docs/i18n/TRANSLATION_GUIDE.md) for terminology and review steps. You can submit a translation update in Russian or English.
