# DeployWitness brand guidelines

## Purpose

DeployWitness makes infrastructure changes easier to review by connecting a configuration change to a checkable contract and its evidence. The visual identity combines an infrastructure graph with a witness point on its path. It deliberately avoids the generic shield-and-checkmark security mark.

## Voice

- **Tagline:** “Know what breaks before you deploy.”
- Lead with a concrete action and output, not a claim of certainty.
- Use **proven configuration break** only for a statically verified violated invariant. Use **risk** when consequences are plausible but not established, and **unknown** when inputs or semantics are incomplete.
- Never imply that the tool predicts every outage, guarantees safe deployment, or reproduces runtime failure today.

## Color

| Token | Color | Use |
| --- | --- | --- |
| Background | `#0B1120` | Dark canvases |
| Surface | `#131E2C` | Cards and panels |
| Primary | `#4CE0CB` | Modeled connections and navigation |
| Text | `#F3F7FA` | Primary text on dark |
| Muted | `#9BB0C4` | Supporting text |
| Warning | `#F4B86D` | Uncertainty and changed evidence |
| Danger | `#F08181` | Confirmed harmful status when needed |
| Light canvas | `#F3F7FA` | Light wordmark background |
| Light primary | `#087F78` | Accessible teal on light backgrounds |

Status must never be communicated by color alone; use its label and explanation too.

## Logo assets

- `assets/brand/wordmark-dark.svg` and `wordmark-light.svg`: horizontal wordmark for dark and light surfaces.
- `assets/brand/mark-dark.svg` and `mark-light.svg`: compact standalone mark.
- `assets/brand/favicon.svg`: browser/app icon.
- `assets/brand/social-preview.svg` and `.png`: 1280 × 640 GitHub social preview artwork.
- `assets/readme/`: original explanatory diagrams, not product screenshots.

Keep clear space around the mark approximately equal to the diameter of one node. Do not recolor status tones, stretch the geometry, add a shield, or place the light wordmark on a dark background. At small sizes, use the compact mark and retain the open center so the trace remains legible.

## Product UI and documentation

Use a neutral dark base with restrained teal. Reserve amber for changed/uncertain evidence. Pair every finding color with a textual confidence status. Prefer diagrams that explain a real modeled relationship, concise copy, and commands verified against the current CLI. Do not publish badges, adoption numbers, benchmarks, or integration claims without evidence.

## Design references

The design review looked at current official pages for [Grafana](https://grafana.com/), [Sentry](https://sentry.io/), [OpenTelemetry](https://opentelemetry.io/), [Infisical](https://infisical.com/), [Turborepo](https://turborepo.com/), and [Trivy](https://trivy.dev/). Useful patterns were a direct first-screen value statement, clear routes to documentation and getting started, product concepts explained with diagrams, and scannable feature sections. DeployWitness uses its own node-and-trace mark, palette, and copy; it does not reuse their assets or visual identity.
