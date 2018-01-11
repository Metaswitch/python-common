ROOT ?= ${PWD}
ENV_DIR := $(shell pwd)/_env
PYTHON_BIN := $(shell which python)

COMPILER_FLAGS := LIBRARY_PATH=. CC="${CC} -Icpp-common/include"
CLEAN_SRC_DIR = .

# We have not written UTs for a number of modules that do not justify it.   Exclude them from coverage results.
COVERAGE_EXCL = **/test/**,metaswitch/common/alarms_writer.py,metaswitch/common/alarms_to_dita.py,metaswitch/common/alarms_to_csv.py,metaswitch/common/stats_to_dita.py,metaswitch/common/generate_stats_csv.py,metaswitch/common/mib.py
COVERAGE_SRC_DIR = metaswitch
COVERAGE_SETUP_PY = setup.py
FLAKE8_INCLUDE_DIR = metaswitch/
BANDIT_EXCLUDE_LIST = metaswitch/common/test,build,_env,eggs,.wheelhouse
include build-infra/python.mk

# The build has been seen to fail on Mac OSX when trying to build on i386. Enable this to build for x86_64 only
X86_64_ONLY=0

.DEFAULT_GOAL = all

.PHONY: all
all: help

.PHONY: help
help:
	@cat README.md

python_common_SETUP = setup.py
python_common_TEST_SETUP = setup.py
python_common_REQUIREMENTS = requirements.txt
python_common_TEST_REQUIREMENTS = requirements.txt requirements-test.txt
python_common_FLAGS = LIBRARY_PATH=. CC="${CC} -Icpp-common/include"
python_common_SOURCES = $(shell find metaswitch -type f -not -name "*.pyc") libclearwaterutils.a
$(eval $(call python_component,python_common))

# Target for building a wheel from this package into the specified wheelhouse
.PHONY: build_common_wheel
build_common_wheel: ${ENV_DIR}/.python_common-install-wheels libclearwaterutils.a
	$(COMPILER_FLAGS) ${PYTHON} setup.py bdist_wheel -d ${WHEELHOUSE}

# python-common's setup.py depends on cffi, so we need to actually install downloaded wheels before we can

VPATH = cpp-common/src:cpp-common/include

%.o: %.cpp $(shell find cpp-common/include -type f)
	g++ -fPIC -o $@ -std=c++0x -Wall -Werror -Icpp-common/include -c $<

libclearwaterutils.a: namespace_hop.o logger.o log.o
	ar cr libclearwaterutils.a $^
