ROOT ?= ${PWD}
ENV_DIR := $(shell pwd)/_env
PYTHON_BIN := $(shell which python)

COMPILER_FLAGS := LIBRARY_PATH=. CC="${CC} -Icpp-common/include"

# The build has been seen to fail on Mac OSX when trying to build on i386. Enable this to build for x86_64 only
X86_64_ONLY=0

.DEFAULT_GOAL = all

.PHONY: all
all: help

.PHONY: help
help:
	@cat README.md

verify:
	flake8 --select=E10,E11,E9,F metaswitch/

style:
	flake8 --select=E,W,C,N --max-line-length=100 metaswitch/

explain-style:
	flake8 --select=E,W,C,N --show-pep8 --first --max-line-length=100 metaswitch/

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
env: ${ENV_DIR}/.eggs_installed

$(ENV_DIR)/bin/python:
	# Set up a fresh virtual environment.
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	$(ENV_DIR)/bin/easy_install "setuptools==24.0.0"
	$(ENV_DIR)/bin/easy_install distribute
	$(ENV_DIR)/bin/pip install cffi

$(ENV_DIR)/bin/coverage: $(ENV_DIR)/bin/python
	$(ENV_DIR)/bin/pip install coverage

.PHONY: build_common_egg
build_common_egg: $(ENV_DIR)/bin/python setup.py libclearwaterutils.a
	$(COMPILER_FLAGS) ${ENV_DIR}/bin/python setup.py bdist_egg -d $(EGG_DIR)

${ENV_DIR}/.eggs_installed : $(ENV_DIR)/bin/python setup.py $(shell find metaswitch -type f -not -name "*.pyc") libclearwaterutils.a
	# Generate .egg files for python-common
	$(COMPILER_FLAGS) ${ENV_DIR}/bin/python setup.py bdist_egg -d .eggs

	# Download the egg files they depend upon
	${ENV_DIR}/bin/easy_install -zmaxd .eggs/ .eggs/*.egg

	# Install the downloaded egg files
	${ENV_DIR}/bin/easy_install --allow-hosts=None -f .eggs/ .eggs/*.egg

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
	rm -rf bin .eggs .develop-eggs parts .installed.cfg bootstrap.py .downloads .buildout_downloads
	rm -rf distribute-*.tar.gz
	rm -rf $(ENV_DIR)
	rm -f metaswitch/common/_cffi.so *.o libclearwaterutils.a


VPATH = cpp-common/src:cpp-common/include

%.o: %.cpp $(shell find cpp-common/include -type f)
	g++ -fPIC -o $@ -std=c++0x -Wall -Werror -Icpp-common/include -c $<

libclearwaterutils.a: namespace_hop.o logger.o log.o
	ar cr libclearwaterutils.a $^
