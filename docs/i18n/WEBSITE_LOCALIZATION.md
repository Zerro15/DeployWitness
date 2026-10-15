# Future website localization

[English](WEBSITE_LOCALIZATION.md) | [Русский](../ru/README.md) · [Documentation index](../README.md)

There is no project website today. Do not add a site generator or JavaScript translation layer just for localization. When a website is approved, build static English and Russian pages suitable for GitHub Pages:

```text
/en/index.html
/en/docs/<page>.html
/ru/index.html
/ru/docs/<page>.html
```

Each page should set the correct document language, localized title/description, and canonical URL, and include reciprocal `hreflang="en"` and `hreflang="ru"` alternate links plus `x-default` where appropriate. Pages should be responsive and work without a backend. The language switch should preserve the current section when that translation exists; otherwise, send the reader to the other language's documentation index. Keep canonical English content as the source of truth and generate both sets of static pages at build time. This is a future architecture note, not a website implementation commitment or an existing feature.
