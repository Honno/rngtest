from .test_examples import Example
from .test_examples import iterexamples


def pytest_addoption(parser):
    parser.addoption(
        "--example", action="store", default=None,
    )


def pytest_generate_tests(metafunc):
    if metafunc.function.__name__ == "test_stattest_on_example":
        title_substr = metafunc.config.getoption("example")
        metafunc.parametrize(Example._fields, iterexamples(title_substr))
