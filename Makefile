# NOTICE:
# This file is intended for executing the project for development and Gitlab CI testing
# it is not intended to be used in Dockerfiles or deployment pipelines


# TODO: outstanding question on whether to load the .env here, or in the project
ifneq ($(wildcard .env),)
	# load our .env
	include .env
	export
endif



# this is needed to make sure `make <command>` does not skip if we have a directory that matches the target name
.PHONY: all setup run test


.DEFAULT: help


help:
	@echo "make setup"
	@echo "         setup virtual environment"
	@echo "make run"
	@echo "         run project"
	@echo "make test"
	@echo "         run linter, unit tests and integration tests"


clean:
	@rm -rf _venv test-output.log coverage .coverage


setup:
	@# remove old venv if it exists
	@if [ -d "_venv" ]; then \
		echo "old venv found, removing"; \
		rm -rf _venv; \
	fi

	@echo "creating venv"
	@python3 -m venv _venv
	@# check if we have a constraints file and use it if we do
	@if [ -f "constraints.txt" ]; then \
		echo "installing requirements with constraints"; \
		./_venv/bin/pip3 install -qqr requirements.txt -r test-requirements.txt -c constraints.txt; \
	else \
		echo "installing requirements"; \
		./_venv/bin/pip3 install -qqr requirements.txt -r test-requirements.txt; \
	fi

run: enforce-setup
	@./_venv/bin/python3 -m src


# optional params: unit=0 (disables unit tests), integration=0 (disables integration tests)
# note: if all tests are skipped, only linting will run, however coverage will report from last run (or error)
test: enforce-setup
	@# run linting on all directories (even if we are only running some tests)
	@./_venv/bin/python -m flake8 --ignore=E501 src test
	@./_venv/bin/python -m unittest test.test_utils_unit


enforce-setup:
	@# checks if venv exists, or creates it and installs packages
	@if [ ! -d "_venv" ]; then \
		echo "venv missing, running setup"; \
		make setup; \
	fi
