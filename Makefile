.PHONY: help run test clean

# Default target
help:
	@echo "Space Battle Duel - Makefile"
	@echo "---------------------------"
	@echo "run   : Start the game"
	@echo "test  : Run all unit tests"
	@echo "help  : Show this help message"
	@echo "clean : Remove python cache files"

run:
	python3 -m src.main

test:
	PYTHONPATH=. python3 -m coverage run --source=src -m unittest discover tests
	python3 -m coverage report -m

test-docs:
	PYTHONPATH=. phmdoctest docs/manual.md --outfile tests/test_manual.py
	PYTHONPATH=. python3 -m pytest tests/test_manual.py
	rm tests/test_manual.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
