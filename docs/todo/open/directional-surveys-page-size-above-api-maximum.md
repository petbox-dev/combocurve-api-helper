# get_directional_surveys sends take=1000; the API maximum is 100

Severity: medium
Opened: 2026-11-05

## What happens now

`get_directional_surveys` (and every caller of it) fails with HTTP 400 before any survey is
returned. `directional.py` sets `GET_LIMIT = 1000` and passes it as `take`.

## Evidence

Live call on the dev tenant, 2026-11-05, helper 2.7.0, `GET /v1/directional-surveys` with a `well`
filter and `take=1000`:

```text
400 {"name":"ValueError","message":"`1000` is out of the valid range. Must be between 1 and 100","details":{"location":"take"}}
```

A downstream MCP server now calls the route with `take=100` through `_get_items_iterator` to work
around this.

## Fix

Set `GET_LIMIT = 100` in `directional.py`. Check `get_directional_surveys` and any other method in
that module that uses the constant.

## What is still unverified

- None for the value: the 3.0.0 checkout has the same `GET_LIMIT = 1000` (`directional.py:5`,
  checked 2026-11-05).
- The query key that filters surveys by well: the dev tenant has no surveys, so `well` was not
  confirmed.

## Files

- `src/combocurve_api_helper/directional.py`: `GET_LIMIT`, `get_directional_surveys`
