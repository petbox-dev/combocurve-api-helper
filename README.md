# ComboCurve API Helper `combocurve-api-helper`

A utility library mapped to ComboCurve's API.

## Petroleum Engineering Toolbox

---

 [![PyPi Version](https://img.shields.io/pypi/v/combocurve-api-helper.svg "PyPi Version")](https://github.com/petbox-dev/combocurve-api-helper)

 [Open in Visual Studio Code](https://open.vscode.dev/petbox-dev/combocurve-api-helper)

## Features

`combocurve-api-helper` wraps the ComboCurve REST API behind a single
`ComboCurveAPI` entrypoint that composes one mixin per resource area:

- **Projects, scenarios, wells** — list / create / update / delete, plus custom
  columns.
- **Production** — daily and monthly volumes.
- **Forecasts & type curves** — read forecasts, write forecast parameters, and
  `put_forecast_parameters_batched()` for parallel, chunked (25 well x phase per
  request), 207-aware bulk writes that return a `BatchWriteResult` (per-record
  `success_count` / `failed_count` / `ok`, results in original payload order).
- **Forecast runs** — submit a forecast run as an async job and poll its status.
- **Econ models** — CREATE / UPDATE / DELETE for econ-model types (project
  per-type and generic; company generics), plus an exact, invertible
  API <-> CSV column mapping for 11 econ-model types.
- **Econ-model assignments** — assign / unassign models to wells per scenario
  qualifier, and read the scenario assignment grid.
- **Lookup tables** — scenario, type-curve, and scenario-assignment CRUD.
- **Econ runs** — trigger scenario economics and read results.
- **Directional** — directional survey access.
- **Resilient transport** — automatic retry with backoff on HTTP 429 (honoring
  `Retry-After`) and transient gateway errors (502 / 503 / 504).

Method docstrings carry an `Example response:` block and a link to the matching
`docs.api.combocurve.com` operation (see [Docstring examples](#docstring-examples)).
See [CHANGELOG.md](CHANGELOG.md) for release history.

### Installation

Install from Python package repository:

```bash
python -m pip install combocurve-api-helper
```

or install directly from GitHub:

```bash
python -m pip install git+https://github.com/petbox-dev/combocurve-api-helper.git@main
```

### Setup

Two files are required in `~/.combocurve`:

- `cc-api.config.json`  
- `combocurve.json`

These are given by ComboCurve when configuring API access. Example files are provided
in `./config-examples/` to demonstrate the expected file structures.

<br>

`cc-api.config.example.json`:
```json
{
    "apikey": "<apikey>"
}
 ```

<br>

`combocurve.example.json`:
```json
{
  "type": "service_account",
  "project_id": "beta-combocurve",
  "private_key_id": "<private_key_id>",
  "private_key": "<private_key>",
  "client_email": "<client_email>",
  "client_id": "<client_id>",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "<client_x509_cert_url>"
}

 ```

## Usage

```python
from combocurve_api_helper import ComboCurveAPI

# Credentials are read from ~/.combocurve (see Setup above)
api = ComboCurveAPI()

# List projects, then scenarios and forecasts within one
projects = api.get_projects()
project_id = projects[0]["id"]

scenarios = api.get_scenarios(project_id)
forecasts = api.get_forecasts(project_id)

# Bulk-write forecast parameters in parallel: chunked and 207-aware
result = api.put_forecast_parameters_batched(project_id, forecast_id, records)
if not result.ok:
    print(f"{result.failed_count} of {len(result.results)} records failed")
```

### Econ models to / from CSV

Each econ-model type has an invertible mapper (`to_csv_rows` / `from_csv_rows`)
looked up by its PascalCase `econModelType`. The mapper's `columns` attribute is
the exact CSV header, and `to_csv_rows` emits one dict per row keyed by those
columns, so a round trip through a CSV file is lossless.

```python
import csv
from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.econ_models import get_mapper

api = ComboCurveAPI()
mapper = get_mapper("Expenses")   # keyed by econModelType (PascalCase)

# --- Read a model from ComboCurve and write it to a CSV ---
model = api.get_expenses_model_by_id(project_id, model_id)
with open("expenses.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=mapper.columns)
    writer.writeheader()
    writer.writerows(mapper.to_csv_rows(model))

# --- Read the CSV back and write the model to ComboCurve ---
with open("expenses.csv", newline="") as f:
    rows = list(csv.DictReader(f))

payload = mapper.from_csv_rows(rows)
api.post_expenses_models(project_id, [payload])   # or put_expenses_models(...) to update
```

## Contributing

1. Fork the repository:
    - On this GitHub page, click "Fork" to create a copy under your own account.

2. CLone the forked repo onto on your machine:
    ```sh
    git clone https://github.com/<your-username>/combocurve-api-helper.git
    cd combocurve-api-helper
    ```

3. Set the upstream remote:
    - This allows you to fetch updates from the original repository:

    ```sh
    git remote add upstream https://github.com/petbox-dev/combocurve-api-helper.git
    ```

4. Create a new branch:
    - Always create a new branch for your feature or fix
    - A common convention is to name the branch your GitHub username, a forward slash, and a brief description of the work you're doing

    ```sh
    git checkout -b <your-username>/<your-branch-name>
    ```

5. Make your changes, and commit:
    - After adding your files, or making edits, ensure typechecking succeeds, then commit your changes

    ```sh
    mypy --package combocurve_api_helper

    git add .
    git commit -m "<description of changes>"
    ```

6. Push to your fork:

    ```sh
    git push origin <the-name-of-your-branch>
    ```

7. Create a pull request:

    - Go to ["Pull Requests" tab](https://github.com/petbox-dev/combocurve-api-helper/compare) in this repo, and click "compare across forks"
    - Choose your branch as the source and keep the default `main` branch as the target
        - ie: `petbox-dev/combocurve-api-helper` (`main`) `<-` `your-username/combocurve-api-helper` (`your-branch-name`)
    - Fill the title and description with a summary of the proposed changes
    - Request a review from `@dsfulf`

## Docstring examples

The `Example response:` / `Example data:` blocks in method docstrings are
**generated from the ComboCurve Postman collection** — do not edit them by hand.
The collection's `<type>` placeholders (`<string>`, `<number>`, `<boolean>`, …)
are filled with realistic, deterministic spoof values (numbers as numbers, bools
as bools, ISO dates, ObjectId-like ids), so a docstring shows the response's
key/value shape without a live API call. Refresh after the API changes:

```sh
python scripts/generate_docstrings.py          # rewrite in place
python scripts/generate_docstrings.py --check   # verify; exit 1 if stale, 2 if unreachable
```

Each method is matched to its operation by the `docs.api.combocurve.com/api/<slug>`
link in its docstring, where `<slug>` is the collection item name. (The OpenAPI
spec at `storage.googleapis.com/beta-combocurve-api-docs/openapi-spec.yaml` has
*real* example values, but is an older/less-complete snapshot — missing ~52
operations as of 2026-07 — so the collection is used instead.)

## Authors

- David Fulford

## License
MIT License

Copyright (c) 2023 Petroleum Engineering Toolbox

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
