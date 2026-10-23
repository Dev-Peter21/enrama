"""Contract boundaries independent of YAML parsing or client filesystem access."""

import pytest


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/a%20b?q=hello%26world#part",
        "HTTPS://EXAMPLE.COM/Case?Q=One#Two",
        "http://localhost:8000/",
        "https://[::1]:443/path",
        "mailto:hello+shop@example.com",
        "MAILTO:hello@example.com",
        "mailto:%22hello%20shop%22@example.com",
        "tel:+5491100000000",
        "TEL:+1",
    ],
)
def test_link_url_preserves_accepted_destination(value: str) -> None:
    from enrama.config._urls import validate_link_url

    assert validate_link_url(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "example.com",
        "/path",
        "//example.com",
        "https:example.com",
        "https:/example.com",
        "https:///example.com",
        "https://",
        "https://:443/",
        "https://user@example.com",
        "https://user:pass@example.com",
        "https://@example.com",
        "https://example.com:abc/",
        "https://example.com:65536/",
        "https://[bad]/",
        "https://exa mple.com/",
        " https://example.com",
        "https://example.com\n",
        "https://example.com/\tbad",
        "https://example.com/\x7f",
        "https://example.com/\x85",
        "https://example.com\\evil",
        "https://example.com/%",
        "https://example.com/%GG",
        "https://example.com/<script>",
        'https://example.com/"bad',
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "java\nscript:alert(1)",
        "javascript&#58;alert(1)",
        "%6Aavascript:alert(1)",
        "https%3A//example.com",
        "data:text/html,hi",
        "file:///etc/passwd",
        "ftp://example.com",
        "tg://example",
        "mailto:",
        "mailto:a@example.com,b@example.com",
        "mailto:Name<a@example.com>",
        "mailto:a@example.com?subject=Hi",
        "mailto:a@example.com?",
        "mailto:a@example.com#x",
        "mailto:a(comment)@example.com",
        "mailto:a%20@example.com",
        "mailto:a%0Ab@example.com",
        "mailto:a%0Db@example.com",
        "mailto:not-an-address",
        "tel:+1?",
        "tel:+1#",
        "tel:1234",
        "tel:+",
        "tel:+54-11",
        "tel:+54;ext=1",
        "tel:+54?x=1",
        "tel:+١٢",
    ],
)
def test_invalid_link_url_is_rejected(value: str) -> None:
    from enrama.config._urls import validate_link_url

    with pytest.raises(ValueError):
        validate_link_url(value)


def test_url_length_boundary() -> None:
    from enrama.config._urls import validate_link_url

    base = "https://example.com/"
    value = base + "a" * (2048 - len(base))
    assert validate_link_url(value) == value
    with pytest.raises(ValueError):
        validate_link_url(value + "a")


@pytest.mark.parametrize(
    "value", ["http://example.com", "mailto:a@example.com", "tel:+1"]
)
def test_https_fields_do_not_inherit_link_protocols(value: str) -> None:
    from enrama.config._urls import validate_https_url, validate_site_url

    for validate in (validate_https_url, validate_site_url):
        with pytest.raises(ValueError):
            validate(value)


def test_site_base_and_social_queries_are_distinct() -> None:
    from enrama.config._urls import validate_https_url, validate_site_url

    assert (
        validate_site_url("https://example.com/client/")
        == "https://example.com/client/"
    )
    for suffix in ("?x=1", "?", "#part", "#"):
        value = "https://example.com/client/" + suffix
        assert validate_https_url(value) == value
        with pytest.raises(ValueError):
            validate_site_url(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("es", "es"),
        ("ES-ar", "es-AR"),
        ("es-419", "es-419"),
        ("ZH-hANT-tw", "zh-Hant-TW"),
        ("sl-ROZAJ", "sl-rozaj"),
        ("de-1901", "de-1901"),
        ("en-Latn-US", "en-Latn-US"),
        ("iw-IL", "iw-IL"),
        ("sh", "sh"),
        ("und", "und"),
    ],
)
def test_language_changes_casing_only(value: str, expected: str) -> None:
    from enrama.config._language import validate_language

    assert validate_language(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "es_AR",
        "Español",
        " es",
        "es ",
        "es-AB",
        "jp",
        "Latn",
        "en-UK",
        "en-000",
        "es-Abcd",
        "sl-rozaj-ROZAJ",
        "en-US-Latn",
        "en-u-ca-gregory",
        "en-x-client",
        "x-client",
        "zh-cmn-Hans",
        "i-klingon",
        "en-foobar",
        "qaa",
        "en-Qaaa",
        "en-AA",
        "en-QM",
        "en-ZZ",
    ],
)
def test_language_rejects_unknown_wrong_category_or_unsupported_subtags(
    value: str,
) -> None:
    from enrama.config._language import validate_language

    with pytest.raises(ValueError):
        validate_language(value)


@pytest.mark.parametrize(
    "value",
    [
        "./assets/logo.png",
        "assets/logo.png",
        "assets/my logo.png",
        "assets/missing.svg",
    ],
)
def test_asset_paths_are_lexical_not_existence_checks(value: str) -> None:
    from enrama.config._paths import validate_asset_path

    assert validate_asset_path(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "/tmp/logo.png",
        "C:/logo.png",
        "C:logo.png",
        "\\logo.png",
        "\\\\server\\share\\logo.png",
        "../logo.png",
        "assets/../logo.png",
        "assets\\..\\logo.png",
        "dist/logo.png",
        "./dist/logo.png",
        "DIST/logo.png",
        "https://example.com/logo.png",
        "data:image/png,a",
        "assets/\x00logo.png",
    ],
)
def test_asset_paths_reject_escape_remote_and_reserved_output(value: str) -> None:
    from enrama.config._paths import validate_asset_path

    with pytest.raises(ValueError):
        validate_asset_path(value)
