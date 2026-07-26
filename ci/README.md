# CI workflow

`github-workflow.yml` is the GitHub Actions workflow for this repo: it runs the
Python and Node test suites and re-checks the bundled Toman price snapshot
against the live catalogue weekly, so a release can never ship a stale price.

It lives here rather than in `.github/workflows/` because the token used for the
first push did not carry the `workflow` scope, and GitHub rejects a push that
creates a workflow file without it.

To enable it, either:

    git mv ci/github-workflow.yml .github/workflows/ci.yml
    git commit -m "ci: enable workflow" && git push

with a token that has the `workflow` scope, or paste the file into
`.github/workflows/ci.yml` through the GitHub web editor, which needs no scope.
