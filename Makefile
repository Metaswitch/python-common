ENV_DIR := $(shell pwd)/_env
PYTHON_BIN := $(shell which python)

# The build has been seen to fail on Mac OSX when trying to build on i386. Enable this to build for x86_64 only
X86_64_ONLY=0

.DEFAULT_GOAL = all

.PHONY: all
all: help

.PHONY: help
help:
	@cat README.md

.PHONY: test
test: $(ENV_DIR)/bin/python setup.py env
	LIBRARY_PATH=. CC="g++ -Icpp-common/include" $(ENV_DIR)/bin/python setup.py test

.PHONY: coverage
coverage: $(ENV_DIR)/bin/coverage setup.py
	rm -rf htmlcov/
	bin/coverage erase
	bin/coverage run --source metaswitch --omit "**/test/**"  setup.py test
	bin/coverage report -m
	bin/coverage html

.PHONY: env
env: ${ENV_DIR}/.eggs_installed

$(ENV_DIR)/bin/python:
	# Set up a fresh virtual environment
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	$(ENV_DIR)/bin/easy_install "setuptools>0.7"
	$(ENV_DIR)/bin/easy_install distribute

${ENV_DIR}/.eggs_installed : $(ENV_DIR)/bin/python setup.py $(shell find metaswitch -type f -not -name "*.pyc") libclearwaterutils.a
	# Generate .egg files for python-common
	LIBRARY_PATH=. CC="gcc -Icpp-common/include" ${ENV_DIR}/bin/python setup.py bdist_egg -d .eggs
	
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
	rm -rf bin eggs develop-eggs parts .installed.cfg bootstrap.py .downloads .buildout_downloads
	rm -rf distribute-*.tar.gz
	rm -rf $(ENV_DIR)
	rm metaswitch/common/_cffi.so *.o libclearwaterutils.a


VPATH = cpp-common/src:cpp-common/include

%.o: %.cpp $(shell find cpp-common/include -type f)
	g++ -fPIC -o $@ -std=c++0x -Wall -Werror -Icpp-common/include -c $<

libclearwaterutils.a: namespace_hop.o logger.o log.o
	ar cr libclearwaterutils.a $^
