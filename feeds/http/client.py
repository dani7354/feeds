import requests
from requests import Response


class HTTPClientBase:
    def get_response_string(self, url: str) -> str:
        pass


class HTTPClient(HTTPClientBase):
    def __init__(self, headers: dict):
        self._headers = headers

    def get_response_string(self, url: str) -> str:
        response = requests.get(url, headers=self._headers)
        if response.status_code != 200:
            return ""

        return self._decode_response(response)

    @staticmethod
    def _decode_response(response: Response) -> str:
        try:
            return response.content.decode(encoding="utf-8")
        except UnicodeDecodeError:
            content_type_header_value = response.headers.get("Content-Type")
            if "ISO-8859-1" in content_type_header_value:
                return response.content.decode(encoding="latin-1")
            else:
                raise
