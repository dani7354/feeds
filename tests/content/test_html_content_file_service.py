import pytest

from feeds.service.content import HtmlContentFileService


@pytest.fixture(name="html_file_service")
def html_file_service(tmp_path) -> HtmlContentFileService:
    return HtmlContentFileService(str(tmp_path), "my_page")


def test_get_diff_different_html_files(html_file_service):
    latest_saved_file_content = """
    <html>
        <body>
            <h1>Test</h1>
        </body>
    </html>
    """
    html_file_service.save_content(latest_saved_file_content.encode())

    new_content = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <h1>Test</h1>
            <p>Some new paragraph...</p>
        </body>
    </html>
    """
    diff = html_file_service.get_diff(new_content)
    assert diff == ""


def test_get_diff_first_content_file(html_file_service):
    new_content = """
    <html>
        <head>
            <title>Test</title>
        </head>
        <body>
            <h1>Test</h1>
            <p>Some new paragraph...</p>
        </body>
    </html>
    """
    diff = html_file_service.get_diff(new_content)
    assert diff == new_content


def test_get_diff_same_html_files(html_file_service):
    latest_saved_file_content = """
    <html>
        <body>
            <h1>Test</h1>
            <p>Some new paragraph...</p>
        </body>
    </html>
    """
    html_file_service.save_content(latest_saved_file_content.encode())

    new_content = """
    <html>
        <body>
            <h1>Test</h1>
            <p>Some new paragraph...</p>
        </body>
    </html>
    """
    diff = html_file_service.get_diff(new_content)
    assert diff == ""
