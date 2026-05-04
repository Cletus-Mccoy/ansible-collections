import pytest

from parsing import parse_getprop, extract_device_info, parse_packages

SAMPLE_GETPROP = """\
[ro.product.manufacturer]: [Google]
[ro.product.model]: [Pixel 7]
[ro.product.brand]: [google]
[ro.build.version.release]: [14]
[ro.build.version.sdk]: [34]
[ro.build.id]: [AP2A.240805.005]
[ro.serialno]: [1A2B3C4D]
[persist.sys.timezone]: [Europe/Brussels]
[persist.sys.locale]: [nl-BE]
[ro.product.name]: [panther]
"""

SAMPLE_PACKAGES = """\
package:com.google.android.apps.maps
package:com.spotify.music
package:com.example.app
"""


class TestParseGetprop:
    def test_parses_known_keys(self):
        props = parse_getprop(SAMPLE_GETPROP)
        assert props["ro.product.manufacturer"] == "Google"
        assert props["ro.product.model"] == "Pixel 7"
        assert props["ro.build.version.sdk"] == "34"

    def test_parses_all_lines(self):
        props = parse_getprop(SAMPLE_GETPROP)
        assert len(props) == 10

    def test_ignores_non_property_lines(self):
        output = "not a property\n[ro.product.brand]: [google]\n"
        props = parse_getprop(output)
        assert list(props.keys()) == ["ro.product.brand"]

    def test_empty_input(self):
        assert parse_getprop("") == {}

    def test_value_with_brackets(self):
        output = "[ro.build.fingerprint]: [google/panther/panther:14/AP2A/release-keys]\n"
        props = parse_getprop(output)
        assert props["ro.build.fingerprint"] == "google/panther/panther:14/AP2A/release-keys"


class TestExtractDeviceInfo:
    def test_extracts_all_fields(self):
        props = parse_getprop(SAMPLE_GETPROP)
        info = extract_device_info(props)
        assert info["manufacturer"] == "Google"
        assert info["model"] == "Pixel 7"
        assert info["brand"] == "google"
        assert info["android_ver"] == "14"
        assert info["sdk_version"] == "34"
        assert info["build_id"] == "AP2A.240805.005"
        assert info["serial"] == "1A2B3C4D"
        assert info["timezone"] == "Europe/Brussels"
        assert info["locale"] == "nl-BE"

    def test_missing_keys_default_to_unknown(self):
        info = extract_device_info({})
        for val in info.values():
            assert val == "unknown"

    def test_partial_props(self):
        info = extract_device_info({"ro.product.model": "Pixel 6"})
        assert info["model"] == "Pixel 6"
        assert info["manufacturer"] == "unknown"


class TestParsePackages:
    def test_parses_package_names(self):
        packages = parse_packages(SAMPLE_PACKAGES)
        assert packages == [
            "com.google.android.apps.maps",
            "com.spotify.music",
            "com.example.app",
        ]

    def test_ignores_non_package_lines(self):
        output = "warning: something\npackage:com.example.app\n"
        assert parse_packages(output) == ["com.example.app"]

    def test_empty_input(self):
        assert parse_packages("") == []
