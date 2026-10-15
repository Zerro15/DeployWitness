# Competitive analysis (October 2026)

This is a scoped comparison of documented capabilities, not a claim that no similar product exists.

| Tool | Documented strength | Gap relative to this MVP |
| --- | --- | --- |
| [Checkov](https://www.checkov.io/7.Scan%20Examples/Terraform%20Plan%20Scanning.html) | IaC policy scanning and Terraform plan JSON | Broad policy checks; a Compose baseline-to-candidate witness for an explicit application contract is a different workflow. |
| [Trivy](https://trivy.dev/docs/latest/scanner/misconfiguration/) | Broad IaC misconfiguration and vulnerability scanning | Focuses on known checks across platforms rather than this narrow contract witness. |
| [Hadolint](https://github.com/hadolint/hadolint) | Dockerfile linting | It targets Dockerfiles, not Compose state changes. |
| [Dockle](https://github.com/goodwithtech/dockle) | Container image best-practice linting | It scans images, not two Compose revisions. |
| [Docker Compose config](https://docs.docker.com/reference/cli/docker/compose/config/) | Merges and renders effective Compose configuration | It validates/renders a candidate but does not explain application-specific changed contracts. |
| [Infracost](https://www.infracost.io/docs/features/cli_commands/) | Terraform cost diffs | Cost is a useful change dimension, not a Compose dependency witness. |
| [env0 plan on PR](https://docs.env0.com/docs/plan-on-pull-request) | Terraform plan feedback in PRs | A plan describes resource changes; it does not establish this Compose contract invariant. |

Real Compose usage illustrates the need for caution: [a profile/`depends_on` issue](https://github.com/docker/compose/issues/10804) and [an override merge issue](https://github.com/docker/compose/issues/11371) show that effective models can be nuanced. Our alpha treats unresolved profiles and overrides conservatively. We have not validated market demand or false-positive rate on real repositories yet.

Technical advantage within scope: a small, offline, inspectable witness that distinguishes declared invariant breaks from risks. The risk is becoming another generic linter; expanding rule count without trustworthy contracts or replay tests would erase the distinction. AI review tools may summarize diffs, but an LLM summary alone is not a deterministic proof; AI is optional and absent here.
