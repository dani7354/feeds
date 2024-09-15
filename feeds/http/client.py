import requests
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class HTTPClientBase:
    def get_response_string(self, url: str) -> str:
        """Should be overwritten by subclasses"""
        raise NotImplementedError

    def get_response_code(self, url: str) -> int:
        """Should be overwritten by subclasses"""
        raise NotImplementedError


class HTTPClientDynamicBase:
    def get_content_by_css_selector(self, url: str, css_selector_loaded: str, css_selector_content: str) -> str:
        """
        Should be overwritten by subclasses
        url: str: URL to get content from
        css_selector_loaded: str: CSS selector to wait for before getting content
        css_selector_content: str: CSS selector to get content from
        """
        raise NotImplementedError


class HTTPClient(HTTPClientBase):
    def __init__(self, headers: dict[str, str]) -> None:
        self._headers = headers
        self._timeout_seconds = 60

    def get_response_string(self, url: str) -> str:
        response = requests.get(url, headers=self._headers, timeout=self._timeout_seconds)
        if response.status_code != 200:
            return ""

        return response.content.decode(encoding="utf-8", errors="ignore")

    def get_response_code(self, url: str) -> int:
        response = requests.get(url, headers=self._headers, timeout=self._timeout_seconds)
        return response.status_code


class HTTPClientDynamic(HTTPClientDynamicBase):
    def __init__(self, headers: dict[str, str]) -> None:
        self._headers = headers
        self._timeout_seconds = 10

    def get_content_by_css_selector(self, url: str, css_selector_loaded: str, css_selector_content) -> str:
        driver_options = Options()
        driver_options.add_argument("--headless")
        with Firefox(options=driver_options) as driver:
            driver.get(url)
            _ = WebDriverWait(driver, timeout=self._timeout_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector_loaded))
            )
            content_html_element = driver.find_element(By.CSS_SELECTOR, css_selector_content)

            return content_html_element.get_attribute("outerHTML")
