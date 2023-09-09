#!/bin/bash


# live_server will throw errors even with live_server_scope=function if I have the live_server setup in different functions
# and I like to restart the server for each test (and have the test cleanup after each test)
# merge request welcome :)


# exit when any command fails
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "private test"
pytest tests/test_xpath_selector.py

echo "RUNNING WITH BASE_URL SET"

# Now re-run some tests with BASE_URL enabled
# Re #65 - Ability to include a link back to the installation, in the notification.
export BASE_URL="https://really-unique-domain.io"


# Re-run with HIDE_REFERER set - could affect login
export HIDE_REFERER=True

# Re-run a few tests that will trigger brotli based storage
export SNAPSHOT_BROTLI_COMPRESSION_THRESHOLD=5
