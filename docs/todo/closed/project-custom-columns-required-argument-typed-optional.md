# get_project_custom_columns types its required argument as Optional

Closed: 2026-11-21 -- settled by: `typing.overload`s on `get_project_custom_columns` and its url builder (`custom_column: str` required; keyword-only `collection` marked `typing_extensions.deprecated`); runtime `TypeError` test and a mypy typing test
If this was wrong, you will see: `tests/test_project_custom_columns_typing.py` failing, or `mypy --strict` accepting `api.get_project_custom_columns(project_id)`

Severity: low
Opened: 2026-11-06

## What happens now

`get_project_custom_columns` and `get_project_custom_columns_url` (`root.py:130`, `root.py:353`)
declare `custom_column: Optional[str] = None`. The argument is required: `_custom_column_argument`
(`root.py:9-22`) raises `TypeError("missing required argument: 'custom_column'")` when it is `None`
and the deprecated alias `collection` is not given. Only the docstrings say that it is required.

A type checker therefore accepts `api.get_project_custom_columns(project_id)`, and the error comes
only at run time.

## Evidence

On 2026-11-05 a downstream MCP server called `get_project_custom_columns(project_id)`. The call
passed `mypy --strict`, and a test fake that copied the `Optional` default hid the error. A task
review found it by reading the helper. On the live API the tool failed on every call. The only
supported value is `'headers'` ("Currently only `headers` is supported", per the docs).

## Why it is `Optional`

2.2.2 renamed the keyword `collection` to `custom_column`. 2.2.x then accepted `collection=` again
as a deprecated alias (CHANGELOG, "`get_project_custom_columns(..., collection=...)` works
again"). Both keywords default to `None`, so that a caller can pass either one. The alias has no
removal date in the CHANGELOG.

## Fix

One of these:

- `typing.overload`: one overload with `custom_column: str` (required) and no `collection`, and one
  with keyword-only `collection: str` that is marked deprecated (`typing_extensions.deprecated`). The
  implementation keeps the current runtime check. A type checker then refuses a call with neither.
- Remove the `collection` alias in a 3.x release, with a removal date and a CHANGELOG entry like the
  other deprecations ("kept until at least 2027-01-31"). Then type `custom_column: str` with no
  default.

Add a test that a call with neither argument raises the `TypeError`. A typing test (for example a
`reveal_type` or an `assert_type` check under mypy) would show that the overloads refuse that call.

## Files

- `src/combocurve_api_helper/root.py`: `_custom_column_argument`, `get_project_custom_columns_url`,
  `get_project_custom_columns`
- `tests/test_root_urls_and_params.py`: the URL tests for this route

## Status (2026-11-21)

Done with the first option. `get_project_custom_columns` and `get_project_custom_columns_url` have
two `typing.overload`s: `custom_column: str` required, or keyword-only `collection: str` marked
`typing_extensions.deprecated`. The implementation keeps `_custom_column_argument` (runtime
`TypeError` for neither or both, `DeprecationWarning` for `collection=`).

- mypy 2.4.1 refuses a call with neither (`call-overload`). It reports the deprecated overload only
  with `--enable-error-code deprecated`; this repo does not enable that code, so a `collection=` call
  passes the repo's own mypy run silently.
- `typing_extensions.deprecated` exists from typing_extensions 4.5.0; `pyproject.toml` lists
  `typing-extensions` with no lower bound. It needs `>=4.5.0`.
- Tests: `tests/test_root_urls_and_params.py` (runtime `TypeError`, nothing sent) and
  `tests/test_project_custom_columns_typing.py` (runs mypy on a snippet; about 50 s cold).
