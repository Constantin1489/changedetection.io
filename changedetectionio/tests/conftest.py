#!/usr/bin/python3

import pytest
from changedetectionio import changedetection_app
from changedetectionio import store
import os
import sys

# https://github.com/pallets/flask/blob/1.1.2/examples/tutorial/tests/test_auth.py
# Much better boilerplate than the docs
# https://www.python-boilerplate.com/py3+flask+pytest/

global app

def cleanup(datastore_path):
    import glob
    # Unlink test output files

    for g in ["*.txt", "*.json", "*.pdf"]:
        files = glob.glob(os.path.join(datastore_path, g))
        for f in files:
            if 'proxies.json' in f:
                # Usually mounted by docker container during test time
                continue
            if os.path.isfile(f):
                os.unlink(f)

@pytest.fixture(scope='session')
def app(request):
    """Create application for the tests."""
    datastore_path = "./test-datastore"

    # So they don't delay in fetching
    os.environ["MINIMUM_SECONDS_RECHECK_TIME"] = "0"
    try:
        os.mkdir(datastore_path)
    except FileExistsError:
        pass

    cleanup(datastore_path)

    app_config = {'datastore_path': datastore_path, 'disable_checkver' : True}
    cleanup(app_config['datastore_path'])

    # Set via Dockerfile ARG and '--build-arg' in test-only.yml
    if os.getenv("LOGGER_LEVEL"):
        logger_level = os.getenv("LOGGER_LEVEL")
    else:
        # a default logger level
        logger_level = 'TRACE'

    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level=logger_level)

    datastore = store.ChangeDetectionStore(datastore_path=app_config['datastore_path'], include_default_watches=False)
    app = changedetection_app(app_config, datastore)

    # Disable CSRF while running tests
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['STOP_THREADS'] = True

    def teardown():
        datastore.stop_thread = True
        app.config.exit.set()
        cleanup(app_config['datastore_path'])

       
    request.addfinalizer(teardown)
    yield app
