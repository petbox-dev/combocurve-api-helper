"""Shared pytest setup: load the repo's gitignored `.env` into the environment.

The live tests (`test_api.py`, `test_assignments_live.py`) read their dev target ids
(`CC_DEV_PROJECT_ID`, `CC_DEV_SCENARIO_ID`, `CC_DEV_DATES_MODEL_ID`) from the environment,
because a real id must not sit in this public repo. `.env.example` lists the names.

`load_dotenv()` searches from this file's directory upward, so the repo-root `.env` is found
whatever the working directory. It never overrides a variable that is already set. This runs
before pytest imports the test modules, which read the ids at import time.
"""

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is a dev dependency; without it the live tests just skip
    pass
else:
    load_dotenv()
