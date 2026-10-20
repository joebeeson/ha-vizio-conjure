from custom_components.vizio_conjure.lovelace import lovelace_path


def test_lovelace_path_matches_cast_style_paths() -> None:
    assert lovelace_path("lovelace", "downstairs") == "/lovelace/downstairs"
    assert lovelace_path("lovelace-cast", "downstairs") == "/lovelace-cast/downstairs"
