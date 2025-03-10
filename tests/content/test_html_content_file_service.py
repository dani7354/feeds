import pytest

from feeds.service.content import HtmlContentFileService


@pytest.fixture(name="html_file_service")
def html_file_service(tmp_path) -> HtmlContentFileService:
    return HtmlContentFileService(str(tmp_path), "my_page")


def count_added_lines(diff: str) -> int:
    return len([x for x in diff.splitlines(keepends=False) if x.startswith("+ ")])


def count_removed_lines(diff: str) -> int:
    return len([x for x in diff.splitlines(keepends=False) if x.startswith("- ")])


def test_get_diff_new_content(html_file_service):
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

    assert count_added_lines(diff) == 4
    assert count_removed_lines(diff) == 0


def test_get_diff_removed_content(html_file_service):
    latest_saved_file_content = """
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
    html_file_service.save_content(latest_saved_file_content.encode())

    new_content = """
    <html>
        <body>
            <h1>Test</h1>
        </body>
    </html>
    """
    diff = html_file_service.get_diff(new_content)

    assert count_removed_lines(diff) == 4
    assert count_added_lines(diff) == 0


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

    assert count_added_lines(diff) == 10
    assert count_removed_lines(diff) == 0


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

    new_content = latest_saved_file_content
    diff = html_file_service.get_diff(new_content)

    assert diff == ""
    assert count_added_lines(diff) == 0
    assert count_removed_lines(diff) == 0


def test_get_diff_escape_html(html_file_service):
    latest_saved_file_content = """
    <html>
        <body>
        </body>
    </html>
    """
    html_file_service.save_content(latest_saved_file_content.encode())

    new_content = """
    <html>
        <body>
            <h1>Test</h1>
        </body>
    </html>
    """
    diff = html_file_service.get_diff(new_content)

    assert count_added_lines(diff) == 1
    assert count_removed_lines(diff) == 0
    map(lambda c: c not in diff, ("<html>", "</html>", "<body>", "</body>", "<h1>", "</h1>"))
