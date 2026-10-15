# Release strategy

DeployWitness follows SemVer. While the package is below `1.0.0`, CLI and witness schema changes may be breaking; document them in `CHANGELOG.md` and announce them in the GitHub Release notes. Use `a`/`b` prerelease versions for early evaluation. Do not imply production readiness from a prerelease tag.

Before a release, run the local test, lint, type, build, wheel-install, and security regression checks on the tagged commit; verify the same commit's GitHub CI result; inspect the built wheel; and confirm documentation examples match the CLI. Create an annotated `vX.Y.Z` tag and a GitHub Release with changed behavior, known limitations, and upgrade notes. Never publish to PyPI automatically; package publication requires separate maintainer authorization.
