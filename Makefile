# Prérequis : uv
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 11 tests analytiques, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

all:              ## fetch + simulate (réseau requis, ~1 min)
	$(UV) run pec fetch
	$(UV) run pec simulate
