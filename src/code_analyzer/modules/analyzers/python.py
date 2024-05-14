import ast
from functools import wraps

from . import CodeAnalyzer


def assert_have_read_content(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if args[0].content is None:
            raise RuntimeError("No content has been read yet.")
        return f(*args, **kwargs)
    return decorator


class PythonASTCodeAnalyzer(CodeAnalyzer):
    def __init__(self):
        super().__init__()
        self.content = None
        self._tree = None

    def read(self, file_path: str):
        with open(file_path, 'r') as f:
            self.content = f.read()
            self._tree = ast.parse(self.content)

    @assert_have_read_content
    def list_imported_packages(self):
        packages = set()
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Import):
                packages.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                packages.add(node.module)
        return packages

    @assert_have_read_content
    def list_all_functions(self):
        raise NotImplementedError()

    @assert_have_read_content
    def contains_test(self):
        packages = self.list_imported_packages()
        if 'unittest' in packages or 'pytest' in packages:
            return True
        for line in self.content:
            # pytest
            if "def test_" in line or "TestCase" in line:
                return True
        return False


class PythonNaiveCodeAnalyzer(CodeAnalyzer):
    def __init__(self):
        super().__init__()
        self.content = None

    def read(self, file_path: str):
        with open(file_path, 'r') as f:
            self.content = f.readlines()

    @assert_have_read_content
    def list_imported_packages(self):
        packages = set()
        for line in self.content:
            if line.startswith('from ') or line.startswith('import '):
                packages.add(line.split()[1].split(".")[0])
            else:
                continue
        return list(packages)

    @assert_have_read_content
    def list_all_functions(self):
        raise NotImplementedError()

    @assert_have_read_content
    def contains_test(self):
        packages = self.list_imported_packages()
        if 'unittest' in packages or 'pytest' in packages:
            return True
        for line in self.content:
            # pytest
            if "def test_" in line or "TestCase" in line:
                return True
        return False

