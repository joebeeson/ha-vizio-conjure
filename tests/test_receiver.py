from custom_components.vizio_conjure.receiver import RECEIVER_HTML


def test_receiver_supports_configurable_focus_styles_and_activation() -> None:
    assert '["off", "outline", "glow"]' in RECEIVER_HTML
    assert "vizio-conjure-focused" in RECEIVER_HTML
    assert "page.interaction" in RECEIVER_HTML
    assert "current.click()" in RECEIVER_HTML
