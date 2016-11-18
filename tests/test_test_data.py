import os
import pytest
from selenium import webdriver

BROWSER = os.environ.get('BROWSER', 'Firefox')

@pytest.fixture(scope="module")
def browser(request):
    browser = getattr(webdriver, BROWSER)()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


def test_1_match(browser):
    browser.get('file://' + os.path.abspath('./output/names.html'))
    assert 'Matches 1' in browser.find_element_by_tag_name('body').text
