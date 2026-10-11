import importlib.resources

import bytesz

# The public API. Add every exported name here as the library grows; this list is the
# contract and the test below fails if the module and this list disagree.
PUBLIC_API: list[str] = [
    "AmbiguousUnitError",
    "ByteszError",
    "InvalidSizeError",
    "format",
    "parse",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(bytesz.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves() -> None:
    for name in bytesz.__all__:
        assert hasattr(bytesz, name)


def test_version_is_a_three_part_string() -> None:
    parts = bytesz.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("bytesz").joinpath("py.typed").is_file()
