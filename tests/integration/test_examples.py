"""Selenium smoke tests against examples/ (server-only mode via utils.get_glue_server).

Covered: 01 hello_world, 03 callbacks, 04 sync_callbacks, 05 file_access,
07 jinja_templates, 10 custom_app_routes.

Not covered here (and why):
- 00 presentation — long interactive demo
- 02 hello_world_chrome — forces mode=chrome; harness overrides mode=None
- 06 input — manual input flow
- 08 createreactapp — needs npm build
- 09 disable_cache — covered at unit level (test_routes)
"""

import os
import time
from tempfile import NamedTemporaryFile, TemporaryDirectory

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.helpers import get_console_logs, get_glue_server


def test_hello_world(driver):
    with get_glue_server('examples/01 - hello_world/hello.py', 'hello.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Hello, World!'

        expected = ('Hello from Javascript World!', 'Hello from Python World!')
        console_logs = get_console_logs(driver, contains=expected)
        messages = [entry['message'] for entry in console_logs]
        for needle in expected:
            assert any(needle in msg for msg in messages), messages


def test_callbacks(driver):
    with get_glue_server('examples/03 - callbacks/callbacks.py', 'callbacks.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Callbacks Demo'

        console_logs = get_console_logs(driver, minimum_logs=1)
        assert 'Got this from Python:' in console_logs[0]['message']
        assert 'callbacks.html' in console_logs[0]['message']


def test_sync_callbacks(driver):
    with get_glue_server(
        'examples/04 - sync_callbacks/sync_callbacks.py', 'sync_callbacks.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Synchronous callbacks'

        console_logs = get_console_logs(driver, minimum_logs=1)
        assert 'Got this from Python:' in console_logs[0]['message']
        assert 'sync_callbacks.html' in console_logs[0]['message']


def test_file_access(driver: webdriver.Remote):
    with get_glue_server(
        'examples/05 - file_access/file_access.py', 'file_access.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Glue Demo'

        with TemporaryDirectory() as temp_dir, NamedTemporaryFile(dir=temp_dir) as temp_file:
            driver.find_element(value='input-box').clear()
            driver.find_element(value='input-box').send_keys(temp_dir)
            time.sleep(0.5)
            driver.find_element(By.CSS_SELECTOR, 'button').click()

            assert driver.find_element(value='file-name').text == os.path.basename(temp_file.name)


def test_jinja_templates(driver: webdriver.Remote):
    with get_glue_server(
        'examples/07 - jinja_templates/hello.py', 'templates/hello.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Hello, World!'

        driver.find_element(By.CSS_SELECTOR, 'a').click()
        WebDriverWait(driver, 2.0).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//h1[text()="This is page 2"]')
            )
        )


def test_custom_app_routes(driver: webdriver.Remote):
    with get_glue_server('examples/10 - custom_app_routes/custom_app.py', 'index.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Hello, World!'

    with get_glue_server('examples/10 - custom_app_routes/custom_app.py', 'custom') as glue_url:
        driver.get(glue_url)
        assert 'Hello, World!' in driver.page_source
