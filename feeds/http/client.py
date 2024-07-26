import requests


class HTTPClientBase:
    def get_response_string(self, url: str) -> str:
        pass


class HTTPClient(HTTPClientBase):
    def __init__(self, headers: dict):
        self._headers = headers

    def get_response_string(self, url: str) -> str:
        response = requests.get(url, headers=self._headers)
        response.encoding = "utf-8"
        if response.status_code == 200:
            return response.content.decode()
        return ""
