.PHONY: help
help: ## This help message
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)"

.PHONY: install
install: ## Install editable into the current environment, with the dev dependency group
	pip install -e . --group dev --config-settings editable_mode=compat

.PHONY: lint
lint: ## Run the repo gate (ruff, ruff format check, mypy) over src tests scripts
	ruff check src tests scripts
	ruff format --check src tests scripts
	mypy src tests scripts

.PHONY: test
test: lint ## Run the gate, then pytest
	pytest

.PHONY: build
build: clean ## Build the wheel and sdist into an empty dist/
	python -m build

.PHONY: publish
publish: test build ## Run the gate, build, then upload this version's wheel and sdist to PyPI
	twine upload -r pypi dist/*

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf build/ dist/ src/combocurve_api_helper.egg-info/
