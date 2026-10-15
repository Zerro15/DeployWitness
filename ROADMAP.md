# Roadmap

All stages run on user-owned compute. Completion requires passing local checks; GitHub Actions may be unavailable due to account billing restrictions.

| Stage | Goal and features | Dependencies | Definition of done and tests | Main risk |
| --- | --- | --- | --- | --- |
| M0 Foundation | Package, CLI, docs, quality gates | None | Install and local checks pass | Packaging drift |
| M1 Static Analysis MVP | Compose discovery, parser, diff, graph, three rule families | M0 | Representative regression fixtures and safe-change tests pass | Incorrect effective Compose model |
| M2 Failure Witness MVP | Machine-readable deterministic witness and replay | M1 | Before fails, candidate breaks, repair passes across rule families | Overstated confidence |
| M3 Developer Experience | Reports and GitHub/GitLab/Forgejo examples | M2 | CI examples tested on owned runners; clear errors | CI-specific behavior |
| M4 Public Beta | Real open-source corpus and false-positive measurement | M3 | Published benchmark method, issues triaged, first beta release | Selection bias |
| M5 Advanced Witness | Optional sandbox reproduction and fix experiments | M4 | Opt-in isolated execution with teardown and security review | Untrusted code execution |
| M6 Expansion | Terraform and Kubernetes adapters | M5 or stable Compose core | Independent adapter tests and schema compatibility | Scope dilution |

Current alpha implements part of M0–M3. Next priorities: robust Compose merge/profile handling, direct contract checks independent of `depends_on`, fuller static-test replay, Git-aware comparison, false-positive corpus, and parser fuzzing. SARIF follows schema stabilization.
