# Translation guide

[English](TRANSLATION_GUIDE.md) | [Русский](../ru/README.md) · [Documentation index](../README.md)

## Languages and source of truth

English is the canonical language for product behavior, CLI options, supported-feature claims, and documentation. Russian is an official, maintained translation. Translate the meaning, not word-for-word phrasing; keep commands, API names, status identifiers, and rule IDs unchanged. When English and Russian differ, the current English source determines intended behavior until the Russian page is corrected.

## File map

- Top-level product pages: `README.md` (English) and `README.ru.md` (Russian).
- Canonical guides: `docs/*.md`.
- Russian guides: `docs/ru/*.md`, paired by topic with canonical guides.
- Glossary: [`GLOSSARY.md`](GLOSSARY.md).
- Future static website approach: [`WEBSITE_LOCALIZATION.md`](WEBSITE_LOCALIZATION.md).

The documentation indexes link to their language counterparts. Use relative links so the switch works in a GitHub checkout and in a future static build.

## Updating a translation

1. Edit the English source first and confirm its technical claim against the CLI or implementation.
2. Update the corresponding Russian page in the same pull request when possible.
3. Keep headings, examples, limitations, warnings, and images aligned. Do not add a capability in Russian that the English source or current code does not provide.
4. Use the glossary for consistent terms and preserve identifiers such as `PROVEN_CONFIG_BREAK`, `POTENTIAL_RISK`, `UNKNOWN`, `NO_FINDING`, and `REPRODUCED_FAILURE` verbatim.
5. Run `python scripts/check_i18n.py`. It checks required files and local links. GitHub Actions warns when an English page changes without its Russian counterpart; this warning is informational and does not fail CI.
6. Ask a fluent reviewer to check technical meaning when the change affects confidence, security, installation, or supported behavior.

Contributors may write issues, questions, and pull requests in Russian. English public titles are preferred for international searchability. No paid translation API or hosted translation service is used.

## Adding another language

Propose a language code and maintainer in an issue. Add a language directory such as `docs/<locale>/`, translated documentation index and README, page switch links, and complete guide pairs. Extend the required-file and freshness mappings in `scripts/check_i18n.py`. Keep English canonical, update the glossary, validate local links, and document any language-specific review ownership. Do not create a separate repository for translations.
