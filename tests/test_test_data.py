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
    browser.get('file://' + os.path.abspath('./output/leads.html'))
    # There should be not matches in the default results
    assert 'Matches' not in browser.find_element_by_tag_name('body').text
    # Click on one of the names sources and another source,
    # and there should be a match
    browser.find_element_by_name('name_sources').click()
    assert 'Matches' not in browser.find_element_by_tag_name('body').text
    browser.find_element_by_name('sources').click()
    assert 'Matches 1' in browser.find_element_by_tag_name('body').text


def test_wards_file(browser):
    browser.get('file://' + os.path.abspath('./output/explore.html'))
    assert 'Matches 11' in browser.find_element_by_tag_name('body').text
    browser.find_element_by_name('sources').click()
    assert 'Matches 2' in browser.find_element_by_tag_name('body').text
