# ComboCurve API Helper `combocurve-api-helper`

A utility library mapped to ComboCurve's API.

## Petroleum Engineering Toolbox

---

 [![PyPi Version](https://img.shields.io/pypi/v/combocurve-api-helper.svg "PyPi Version")](https://github.com/petbox-dev/combocurve-api-helper)

 [Open in Visual Studio Code](https://open.vscode.dev/petbox-dev/combocurve-api-helper)

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
