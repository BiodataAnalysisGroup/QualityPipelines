# Integrate in GitHub Actions

resqui ships as a reusable GitHub Action. Add it to any repository to run
quality assessments automatically on every push.

## Prerequisites

1. Go to your repository → **Settings → Actions → General** and ensure
   "Allow all actions and reusable workflows" is selected.

2. Create an environment called **resqui** at
   `https://github.com/USER_OR_GROUP/PROJECT/settings/environments`.

3. Add a secret named `DASHVERSE_TOKEN` to that environment (obtain it from
   your DashVerse instance). If you do not have a DashVerse token the step
   will report a failure but the assessment itself still runs.

## Minimal workflow

Create `.github/workflows/resqui.yml` in your repository:

```yaml
name: Run resqui

on:
  push:

jobs:
  run-resqui:
    runs-on: ubuntu-latest
    environment: resqui

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run resqui action
        uses: EVERSE-ResearchSoftware/QualityPipelines@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          dashverse_token: ${{ secrets.DASHVERSE_TOKEN }}
```

## Using a custom configuration

Place a config file (e.g. `.resqui.json`) at the root of your repository and
pass its path to the action:

```yaml
      - name: Run resqui action
        uses: EVERSE-ResearchSoftware/QualityPipelines@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          dashverse_token: ${{ secrets.DASHVERSE_TOKEN }}
          config: .resqui.json
```

## Running the CLI directly

If you prefer managing the installation yourself:

```yaml
      - name: Install resqui
        run: pip install resqui

      - name: Run resqui
        run: resqui -t ${{ secrets.GITHUB_TOKEN }} -d ${{ secrets.DASHVERSE_TOKEN }}
```

## Uploading to a self-hosted DashVerse

By default results are uploaded to the public instance at
`https://api.dashverse.cloud`. To upload to your own DashVerse, point resqui at
its PostgREST endpoint with `-e` or the `DASHVERSE_ENDPOINT` environment
variable. The token must be issued by that same instance.

```yaml
      - name: Run resqui
        env:
          DASHVERSE_ENDPOINT: ${{ vars.DASHVERSE_ENDPOINT }}  # e.g. http://192.168.1.10:3000
        run: resqui -t ${{ secrets.GITHUB_TOKEN }} -d ${{ secrets.DASHVERSE_TOKEN }}
```

If the instance is only reachable from a private network, run the job on a
[self-hosted runner](https://docs.github.com/en/actions/hosting-your-own-runners)
inside that network (`runs-on: self-hosted`).
