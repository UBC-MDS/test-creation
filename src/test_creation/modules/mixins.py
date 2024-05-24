import os
from abc import ABC, abstractmethod

import pypandoc


class WriteableMixin:
    """A mixin for classes which will write content to filesystem."""
    def _filedump_check(self, output_path: str, exist_ok: bool, expects_directory_if_exists: bool = False):
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"Write permission is not granted for the output path: {output_path}")
        if not exist_ok and os.path.exists(output_path):
            raise FileExistsError("Output file already exists. Use `exist_ok=True` to overwrite.")
        else:
            if expects_directory_if_exists and os.path.isfile(output_path):
                raise NotADirectoryError("An object already exists in the path, expecting a directory but it is a file.")
            elif not expects_directory_if_exists and os.path.isdir(output_path):
                raise IsADirectoryError("An object already exists in the path, expecting a file but it is a directory.")
        return True


class ExportableMixin(WriteableMixin, ABC):
    """A mixin that provides functionality to export (dump) content as HTML/PDF/Quarto documents.

    Extends WriteableMixin.

    Relies on markdown representations of the object.
    The class including mixin must have `.as_markdown()` and `.as_quarto_markdown()` implemented.
    """
    @abstractmethod
    def as_markdown(self) -> str:
        pass

    @abstractmethod
    def as_quarto_markdown(self) -> str:
        pass

    @staticmethod
    def _escape_single_quotes(string: str) -> str:
        return string.replace("'", "\\'")

    def export_html(self, output_path: str, exist_ok: bool = False):
        self._filedump_check(output_path, exist_ok)
        pypandoc.convert_text(self._escape_single_quotes(self.as_markdown()), 'html', format='md',
                              outputfile=output_path)

    def export_pdf(self, output_path: str, exist_ok: bool = False):
        self._filedump_check(output_path, exist_ok)
        pypandoc.convert_text(self.as_markdown(), 'pdf', format='md', outputfile=output_path,
                              extra_args=['--pdf-engine=tectonic'])

    def export_quarto(self, output_path: str, exist_ok: bool = False):
        self._filedump_check(output_path, exist_ok)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.as_quarto_markdown())
