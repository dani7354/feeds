import logging
import os.path
from datetime import datetime
from difflib import unified_diff


class ContentFileServiceBase:
    date_format = "%Y-%m-%d-%H-%M-%S"

    def __init__(self, content_dir_path: str):
        self.content_dir_path = content_dir_path
        self.logger = logging.getLogger("ContentFileService")
        self._create_content_dir_if_not_exists()

    @property
    def saved_content_count(self) -> int:
        raise NotImplementedError

    def save_content(self, content: bytes) -> None:
        filename = self.get_new_filename()
        file_path = os.path.join(self.content_dir_path, filename)
        with open(file_path, "wb") as file:
            self.logger.debug("Writing content to %s...", file_path)
            file.write(content)

    def read_latest_content(self) -> bytes | None:
        content_files = self._list_content_dir()
        if not content_files:
            return None

        file_path = os.path.join(self.content_dir_path, content_files[0])
        self.logger.debug("Reading content from %s...", file_path)
        with open(file_path, "rb") as file:
            return file.read()

    def get_new_filename(self) -> str:
        """Should be overwritten by subclasses"""
        raise NotImplementedError

    def _create_content_dir_if_not_exists(self) -> None:
        if os.path.exists(self.content_dir_path):
            return
        self.logger.debug("Creating content directory %s", self.content_dir_path)
        os.makedirs(self.content_dir_path)

    def clean_up_content_dir(self) -> None:
        saved_content = self._list_content_dir()
        if len(saved_content) > self.saved_content_count:
            for file in saved_content[self.saved_content_count:]:
                file_path = os.path.join(self.content_dir_path, file)
                self.logger.debug("Removing file %s...", file_path)
                os.remove(file_path)

    def _list_content_dir(self) -> list[str]:
        return sorted(os.listdir(self.content_dir_path), reverse=True)


class HtmlContentFileService(ContentFileServiceBase):

    def __init__(self, content_dir: str, base_filename: str):
        super().__init__(content_dir)
        self.base_filename = base_filename

    @property
    def saved_content_count(self) -> int:
        return 50

    def get_new_filename(self) -> str:
        return f"{self.base_filename}_{datetime.now().strftime(self.date_format)}.html"

    def get_diff(self, new_content: str) -> str | None:
        latest_content = self.read_latest_content().decode(errors="ignore")
        if not latest_content:
            return None

        diff_content = unified_diff(
            latest_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile="Latest saved content",
            tofile="New content")

        return "".join(diff_content)
