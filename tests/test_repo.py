from pathlib import Path
from contextlib import nullcontext as does_not_raise

import pytest
from test_creation.modules.code_analyzer import repo as r
from test_creation.modules.code_analyzer.git import GitContext


@pytest.fixture()
def test_git_repo(git_repo):
    # The fixture derives from `workspace` in `pytest-shutil`, so they contain
    # a handle to the path `path` object (see https://path.readthedocs.io/)
    path = git_repo.workspace
    txt_file = path / 'hello.txt'
    txt_file.write_text('hello world!')

    py_file = Path(path / 'src/python/main.py')
    py_file.parent.mkdir(parents=True, exist_ok=True)
    py_file.write_text('print("hello world!")')

    # We can run commands relative to the working directory
    git_repo.run('git add .')

    # It's better to use the GitPython api directly - the 'api' attribute is
    # a handle to the repository object.
    git_repo.api.index.commit("Initial commit")

    # The fixture has a URI property you can use in downstream systems
    assert git_repo.uri.startswith('file://')

    return git_repo


################################################################################
# Repository                                                                   #
################################################################################
def test_repository_should_be_able_to_read_git_repo(test_git_repo):
    path = test_git_repo.workspace
    repo = r.Repository(path)
    assert any(['src/python/main.py' in file for file in repo._get_all_files()])


@pytest.mark.parametrize(
    "fixture_name, dirs_input, expected_result, expectation",
    [
        ("test_git_repo", ["src", "./src/python"], ["src"], does_not_raise()),
        ("test_git_repo", ["~/.vimrc"], [], pytest.raises(FileNotFoundError)),
        ("test_git_repo", ["./src/python/main.py"], [], pytest.raises(NotADirectoryError)),
        ("test_git_repo", ["..", "../.."], [], pytest.raises(ValueError)),
        ("test_git_repo", ["/non/existent/path"], [], pytest.raises(FileNotFoundError)),
    ],
)
def test_repository_normalize_dirs_works_as_expected(fixture_name, dirs_input,
                                                     expected_result,
                                                     expectation, request):
    path = request.getfixturevalue(fixture_name).workspace
    repo = r.Repository(path)
    with expectation:
        assert repo.normalize_dirs(dirs_input) == [repo.root / dir for dir in expected_result]


################################################################################
# GitContext                                                                   #
################################################################################
@pytest.mark.parametrize(
    "fixture_name, remote_name, remote_url, expected",
    [
        (
                "test_git_repo",
                "origin",
                "git@github.internal.com:UBC-MDS/testing-repo_1234.git",
                ("github.internal.com", "UBC-MDS", "testing-repo_1234")
        ),
        (
                "test_git_repo",
                "export",
                "ssh://git@github.internal.com:UBC-MDS/testing-repo_1234.git",
                ("github.internal.com", "UBC-MDS", "testing-repo_1234")
        ),
        (
                "test_git_repo",
                "internal",
                "https://github.com:8080/UBC-MDS/test-creation.git",
                ("github.com:8080", "UBC-MDS", "test-creation")
        ),
        (
                "test_git_repo",
                "origin",
                "http://gitlab.example.com:8080/UBC-MDS/test-creation.git",
                ("gitlab.example.com:8080", "UBC-MDS", "test-creation")
        ),
        (
                "test_git_repo",
                "a",
                "ftp://github.com/SoloSynth1/Solosynth1",
                ("github.com", "SoloSynth1", "Solosynth1")
        ),
    ]
)
def test_git_context_can_extract_remote_git_urls(fixture_name, remote_name,
                                                 remote_url, expected, request):
    repo = request.getfixturevalue(fixture_name)
    repo.api.create_remote(remote_name, remote_url)
    gc = GitContext(repo.workspace)
    assert (gc.host, gc.org, gc.repo_name) == expected


def test_git_context_gives_out_local_link_when_no_remote(test_git_repo):
    context = GitContext(test_git_repo.workspace)
    link = context.construct_remote_link_to_file("src/python/main.py")
    assert link == f"file://{test_git_repo.workspace}/src/python/main.py"