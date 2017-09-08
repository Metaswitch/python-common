ROOT ?= ${PWD}
ENV_DIR := $(shell pwd)/_env
PYTHON_BIN := $(shell which python)

COMPILER_FLAGS := LIBRARY_PATH=. CC="${CC} -Icpp-common/include"

FLAKE8 := ${ENV_DIR}/bin/flake8

# The build has been seen to fail on Mac OSX when trying to build on i386. Enable this to build for x86_64 only
X86_64_ONLY=0

.DEFAULT_GOAL = all

.PHONY: all
all: help

.PHONY: help
help:
	@cat README.md

verify: ${FLAKE8}
	${FLAKE8} --select=E10,E11,E9,F metaswitch/

style: ${FLAKE8}
	${FLAKE8} --select=E,W,C,N --max-line-length=100 metaswitch/

explain-style: ${FLAKE8}
	${FLAKE8} --select=E,W,C,N --show-pep8 --first --max-line-length=100 metaswitch/

.PHONY: test
test: $(ENV_DIR)/bin/python setup.py env
	$(COMPILER_FLAGS) $(ENV_DIR)/bin/python setup.py test

# We have not written UTs for a number of modules that do not justify it.   Exclude them from coverage results.
NO_COVERAGE="metaswitch/common/alarms_writer.py,metaswitch/common/alarms_to_dita.py,metaswitch/common/alarms_to_csv.py,metaswitch/common/stats_to_dita.py,metaswitch/common/generate_stats_csv.py,metaswitch/common/mib.py"

.PHONY: coverage
coverage: $(ENV_DIR)/bin/coverage setup.py env
	rm -rf htmlcov/
	_env/bin/coverage erase
	$(COMPILER_FLAGS) _env/bin/coverage run --source metaswitch --omit "**/test/**,$(NO_COVERAGE)"  setup.py test
	_env/bin/coverage report -m --fail-under 100
	_env/bin/coverage html

.PHONY: env
env: ${ENV_DIR}/.wheels_installed

${FLAKE8}: ${ENV_DIR}/bin/python
	${ENV_DIR}/bin/pip install flake8

$(ENV_DIR)/bin/python:
	# Set up a fresh virtual environment.
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	$(ENV_DIR)/bin/easy_install "setuptools==24"
	$(ENV_DIR)/bin/easy_install distribute
	$(ENV_DIR)/bin/pip install cffi

$(ENV_DIR)/bin/coverage: $(ENV_DIR)/bin/python
	$(ENV_DIR)/bin/pip install coverage

.PHONY: build_common_wheel
build_common_wheel: $(ENV_DIR)/bin/python setup.py libclearwaterutils.a
	$(COMPILER_FLAGS) ${ENV_DIR}/bin/pip wheel -w ${WHEELHOUSE} -r requirements.txt .

${ENV_DIR}/.wheels_installed : $(ENV_DIR)/bin/python setup.py requirements.txt $(shell find metaswitch -type f -not -name "*.pyc") libclearwaterutils.a
	rm -rf .wheelhouse

	# Generate .whl files for python-common and dependencies
	$(COMPILER_FLAGS) ${ENV_DIR}/bin/pip wheel -w .wheelhouse -r requirements.txt .

	# Install the downloaded wheels
	${ENV_DIR}/bin/pip install --compile \
							   --no-index \
							   --upgrade \
							   --force-reinstall \
							   --find-links=.wheelhouse \
							   metaswitchcommon

	# Touch the sentinel file
	touch $@

.PHONY: clean
clean: envclean pyclean

.PHONY: pyclean
pyclean:
	find . -name \*.pyc -exec rm -f {} \;
	rm -rf *.egg-info dist
	rm -f .coverage
	rm -rf htmlcov/

.PHONY: envclean
envclean:
	rm -rf bin .wheelhouse .wheels_installed .develop-eggs parts .installed.cfg bootstrap.py .downloads .buildout_downloads
	rm -rf distribute-*.tar.gz
	rm -rf $(ENV_DIR)
	rm -f metaswitch/common/_cffi.so *.o libclearwaterutils.a


VPATH = cpp-common/src:cpp-common/include

%.o: %.cpp $(shell find cpp-common/include -type f)
	g++ -fPIC -o $@ -std=c++0x -Wall -Werror -Icpp-common/include -c $<

libclearwaterutils.a: namespace_hop.o logger.o log.o
	ar cr libclearwaterutils.a $^

BANDIT_EXCLUDE_LIST = metaswitch/common/test,build,_env,.eggs
include build-infra/python.mk
