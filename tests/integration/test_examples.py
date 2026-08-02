"""Selenium smoke tests against examples/ (server-only mode via utils.get_glue_server).

Covered: 01 hello_world, 03 callbacks, 04 sync_callbacks, 05 file_access,
06 input, 07 jinja_templates, 10 custom_app_routes.

Not covered here (and why):
- 00 presentation — long interactive demo
- 02 hello_world_chrome — forces mode=chrome; harness overrides mode=None
- 08 createreactapp — needs npm build
- 09 disable_cache — covered at unit level (test_routes)
- 11 splash — native GLFW process/window behavior
- 12 scrolling — native title-bar layout behavior
"""

import os
from tempfile import NamedTemporaryFile, TemporaryDirectory

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from tests.helpers import get_console_logs, get_glue_server


def test_hello_world(driver):
    with get_glue_server('examples/01 - hello_world/hello_world.py', 'index.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Hello, World!'

        expected = (
            'JavaScript received: Hello from JavaScript World!',
            'JavaScript received: Hello from Python World!',
        )
        console_logs = get_console_logs(driver, contains=expected)
        messages = [entry['message'] for entry in console_logs]
        for needle in expected:
            assert any(needle in msg for msg in messages), messages


def test_callbacks(driver):
    with get_glue_server('examples/03 - callbacks/callbacks.py', 'index.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Callbacks Demo'

        console_logs = get_console_logs(driver, contains=('Python random callback:',))
        assert any('Python random callback:' in entry['message'] for entry in console_logs)


def test_sync_callbacks(driver):
    with get_glue_server(
        'examples/04 - sync_callbacks/sync_callbacks.py', 'index.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Synchronous callbacks'

        console_logs = get_console_logs(driver, minimum_logs=1)
        assert 'Got this from Python:' in console_logs[0]['message']
        assert 'app.js' in console_logs[0]['message']


def test_file_access(driver: webdriver.Remote):
    with get_glue_server('examples/05 - file_access/file_access.py', 'index.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Python file access'

        with TemporaryDirectory() as temp_dir, NamedTemporaryFile(dir=temp_dir) as temp_file:
            expected = os.path.basename(temp_file.name)
            driver.find_element(value='folder').clear()
            driver.find_element(value='folder').send_keys(temp_dir)
            driver.find_element(By.CSS_SELECTOR, 'button').click()
            WebDriverWait(driver, 2.0).until(
                expected_conditions.text_to_be_present_in_element((By.ID, 'file-name'), expected)
            )


def test_input(driver: webdriver.Remote):
    with get_glue_server('examples/06 - input/input.py', 'index.html') as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Input bridge'

        driver.find_element(value='value').send_keys('bridge test')
        driver.find_element(By.CSS_SELECTOR, 'button').click()
        WebDriverWait(driver, 2.0).until(
            expected_conditions.text_to_be_present_in_element(
                (By.ID, 'result'), 'Received by Python: bridge test'
            )
        )


def test_jinja_templates(driver: webdriver.Remote):
    with get_glue_server(
        'examples/07 - jinja_templates/jinja_templates.py', 'templates/index.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Jinja templates'

        driver.find_element(By.CSS_SELECTOR, 'a').click()
        WebDriverWait(driver, 2.0).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//h1[text()="This is page two."]')
            )
        )


def test_custom_app_routes(driver: webdriver.Remote):
    with get_glue_server(
        'examples/10 - custom_app_routes/custom_app_routes.py', 'index.html'
    ) as glue_url:
        driver.get(glue_url)
        assert driver.title == 'Custom Bottle routes'
        driver.find_element(value='load-route').click()
        WebDriverWait(driver, 2.0).until(
            expected_conditions.text_to_be_present_in_element(
                (By.ID, 'result'), 'Hello from a custom Bottle route'
            )
        )

    with get_glue_server(
        'examples/10 - custom_app_routes/custom_app_routes.py', 'custom'
    ) as glue_url:
        driver.get(glue_url)
        assert 'Hello from a custom Bottle route' in driver.page_source
