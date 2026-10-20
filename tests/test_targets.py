import pytest

from custom_components.vizio_conjure.targets import find_target, parse_targets, targets_json


def test_targets_round_trip_and_lookup() -> None:
    targets = parse_targets(
        [
            {"name": "Smoke", "kind": "url", "url": "http://tv-page.local/"},
            {
                "name": "Downstairs",
                "kind": "lovelace",
                "dashboard_path": "lovelace-cast",
                "view_path": "downstairs",
            },
        ]
    )

    assert find_target(targets, "smoke").url == "http://tv-page.local/"
    assert parse_targets(targets_json(targets)) == targets


@pytest.mark.parametrize(
    "value",
    [
        [{"name": "bad", "kind": "url", "url": "file:///tmp/page"}],
        [{"name": "bad", "kind": "lovelace"}],
        [
            {"name": "same", "kind": "url", "url": "http://one/"},
            {"name": "SAME", "kind": "url", "url": "http://two/"},
        ],
    ],
)
def test_targets_reject_invalid_records(value: object) -> None:
    with pytest.raises(ValueError):
        parse_targets(value)
