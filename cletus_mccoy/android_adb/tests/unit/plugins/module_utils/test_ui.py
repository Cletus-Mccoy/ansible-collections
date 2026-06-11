import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils import ui


SAMPLE = '''<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.settings" bounds="[0,0][1080,2400]">
    <node index="0" text="OK" resource-id="android:id/button1" content-desc="" class="android.widget.Button" package="com.android.settings" clickable="true" bounds="[100,200][300,260]" />
    <node index="1" text="Cancel" resource-id="android:id/button2" content-desc="" class="android.widget.Button" package="com.android.settings" clickable="true" bounds="[400,200][600,260]" />
  </node>
</hierarchy>'''


def test_parse_bounds():
    assert ui.parse_bounds("[100,200][300,260]") == (100, 200, 300, 260)
    assert ui.parse_bounds("garbage") is None


def test_center_of():
    assert ui.center_of("[100,200][300,260]") == (200, 230)
    assert ui.center_of("") is None


def test_parse_nodes():
    nodes = ui.parse_nodes(SAMPLE)
    # 3 <node> elements
    assert len(nodes) == 3
    ok = [n for n in nodes if n["text"] == "OK"][0]
    assert ok["resource_id"] == "android:id/button1"
    assert ok["clickable"] is True
    assert ok["center"] == (200, 230)


def test_find_nodes_by_text():
    nodes = ui.parse_nodes(SAMPLE)
    hits = ui.find_nodes(nodes, text="Cancel")
    assert len(hits) == 1
    assert hits[0]["center"] == (500, 230)


def test_find_nodes_by_resource_id():
    nodes = ui.parse_nodes(SAMPLE)
    hits = ui.find_nodes(nodes, resource_id="android:id/button1")
    assert len(hits) == 1
    assert hits[0]["text"] == "OK"


def test_find_nodes_no_criteria_returns_empty():
    nodes = ui.parse_nodes(SAMPLE)
    assert ui.find_nodes(nodes) == []
