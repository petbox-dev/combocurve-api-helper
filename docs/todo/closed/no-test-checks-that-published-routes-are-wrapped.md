Closed: 2026-11-12 -- settled by: `tests/test_published_routes_are_wrapped.py` (call-based audit with a reviewed `_UNWRAPPED` list)
If this was wrong, you will see: a route that ComboCurve adds to the Postman collection with no method, and the test still passes.

# No test checks that published routes are wrapped

Severity: low
Opened: 2026-11-05

## What happened

The list in `published-routes-without-a-method.md` came from a one-time audit. No test repeated it.
A new published route stayed unnoticed until a person compared the collection with the code.

## Decision

Approved 2026-11-05, for after 3.0.0. Built 2026-11-12 (3.1.0).

## What the test does

`tests/test_published_routes_are_wrapped.py` calls every public method of `ComboCurveAPI` on a fake
transport with placeholder arguments and records each (verb, path) it sends. A by-type method
(`econ_model_type`) is called once per econ-model type. A collection path parameter (`:name`) matches
any one sent segment, because the collection also writes literal-valued parameters that way
(`:econName`, `:collection`). It fails when:

- a collection operation is reached by no method and is not in `_UNWRAPPED` (a new route);
- an `_UNWRAPPED` entry is now reached (a stale entry);
- a public method sends nothing, other than the pure helpers in `_SENDS_NOTHING_BY_DESIGN` (it needs
  an `_ARGUMENT_OVERRIDES` entry).

Network-gated: it skips when the collection cannot be fetched.

## State on 2026-11-12

502 collection operations; 97 in `_UNWRAPPED`: the 79 of `published-routes-without-a-method.md`, the
17 retired v1 type-curve routes, and `POST /v1/oauth/token` (`auth.py` posts to it directly). The v2
type-curve operations are now in the collection, and every one is reached. Both failure assertions
were checked by hand with a modified copy of the list.

## Limit

A method is credited with a route when it sends that verb and path. The test does not check the body
or the query.
