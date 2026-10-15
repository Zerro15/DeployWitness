# Technical glossary

[English](GLOSSARY.md) | [Русский](../ru/README.md) · [Documentation index](../README.md)

| English term | Preferred Russian wording | Usage note |
| --- | --- | --- |
| Failure Witness | свидетельство нарушения (Failure Witness) | Structured static evidence. Avoid suggesting an observed runtime failure. |
| Configuration Contract | конфигурационный контракт | An explicit, machine-checkable invariant. |
| Proven Configuration Break | доказанное нарушение конфигурационного контракта | Does not mean a runtime outage was reproduced. |
| Potential Risk | потенциальный риск | Relevant change without sufficient proof of a broken contract. |
| Unknown | недостаточно данных для вывода (`UNKNOWN`) | Use for unsupported or unresolved input semantics. |
| No Finding | проблем не обнаружено среди проверенных правил (`NO_FINDING`) | Never paraphrase as “safe” or “valid”. |
| Reproduced Failure | воспроизведённый сбой (`REPRODUCED_FAILURE`) | Reserved status; not emitted by the current alpha. |
| Base | базовая версия / базовая конфигурация | The state being compared against. |
| Head | новая версия / кандидат | The configuration being evaluated. |
| Runner | исполнитель CI (runner) | User-owned machine or CI worker. |
| Bind mount | bind mount / подключение каталога хоста | Use “путь источника bind mount” when the host path matters. |

Machine identifiers, commands, option names, YAML keys, and rule IDs are never translated.
