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

# TODO This repository doesn't have full code coverage - it should. Some files
# are temporarily excluded from coverage to make it easier to detect future
# regressions. We should fix up the coverage when we can
EXTRA_COVERAGE="metaswitch/common/logging_config.py,metaswitch/common/phonenumber_utils.py,metaswitch/common/simservs.py,metaswitch/common/ifcs.py"

.PHONY: coverage
coverage: $(ENV_DIR)/bin/coverage setup.py env
	rm -rf htmlcov/
	_env/bin/coverage erase
	$(COMPILER_FLAGS) _env/bin/coverage run --source metaswitch --omit "**/test/**,metaswitch/common/alarms_writer.py,$(EXTRA_COVERAGE)"  setup.py test
	_env/bin/coverage report -m --fail-under 100
	_env/bin/coverage html

.PHONY: env
env: ${ENV_DIR}/.eggs_installed

$(ENV_DIR)/bin/python:
	# Set up a fresh virtual environment
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	# We need to pull down >= 17.1 as Mock depends on it. We should probably find out why it wasn't working when set to version 0.7, as mock should have pulled what it needed.
	$(ENV_DIR)/bin/easy_install "setuptools>=17.1"
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
