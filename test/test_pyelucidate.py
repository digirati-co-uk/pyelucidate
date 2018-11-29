"""
Tests for `pyelucidate` module.
"""
from pyelucidate import pyelucidate as elucidate
import json
import requests_mock
import types
import os
import pytest


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def test_set_query_field():
    test_uri = (
        "https://elucidate.example.org/annotation/w3c/services/search/target?"
        + "page=0&fields=id&value=https%3A%2F%2Fwww.example.org%2Fiiif%2Fproj%2Fc1&desc=1"
    )
    result_uri = (
        "https://elucidate.example.org/annotation/w3c/services/search/target?fields=id&value="
        + "https%3A%2F%2Fwww.example.org%2Fiiif%2Fproj%2Fc1&desc=1&page=2"
    )
    assert (
        elucidate.set_query_field(test_uri, field="page", value=2, replace=True)
        == result_uri
    )


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "page_mock.json"))
def test_annotation_pages(datafiles):
    path = str(datafiles)
    with open(os.path.join(path, "page_mock.json"), "r") as f:
        j = json.load(f)
        test_list = list(elucidate.annotation_pages(j))
        result_last = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=source&value="
            + "https%3A%2F%2Fomeka.example.org%2Fs%2Fexample%2Fpage%2Ftopics%2Fschool%2F&desc=1&page=31"
        )
        assert test_list[-1] == result_last


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "empty_page_mock.json"))
def test_empty_annotation_pages(datafiles):
    path = str(datafiles)
    with open(os.path.join(path, "empty_page_mock.json"), "r") as f:
        j = json.load(f)
        test_list = list(elucidate.annotation_pages(j))
        assert test_list == []


def test_no_annotation_pages():
    test_list = list(elucidate.annotation_pages(result=None))
    assert test_list == []


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_topic_page.json"),
    os.path.join(FIXTURE_DIR, "single_topic_page0.json"),
    os.path.join(FIXTURE_DIR, "single_anno.json"),
)
def test_items_by_body_source(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_topic_page.json"), "r") as f:
            j = json.load(f)
        with open(os.path.join(path, "single_topic_page0.json"), "r") as f:
            j0 = json.load(f)
        with open(os.path.join(path, "single_anno.json"), "r") as f:
            j1 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.register_uri(
            "GET", url, json=j
        )  # mocking the http response within this context
        mock.register_uri(
            "GET", url2, json=j0
        )  # mocking the http response within this context
        response = elucidate.items_by_body_source(
            elucidate="https://elucidate.example.org",
            topic="https://omeka.example.org/topic/virtual:person/matter",
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 23
        assert anno_list[3] == j1


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_topic_page.json"),
    os.path.join(FIXTURE_DIR, "single_topic_page0.json"),
)
def test_items_by_body_source_error(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_topic_page.json"), "r") as f:
            j = json.load(f)
        with open(os.path.join(path, "single_topic_page0.json"), "r") as f:
            j0 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.register_uri(
            "GET", url, json=j, status_code=500
        )  # mocking the http response within this context
        mock.register_uri(
            "GET", url2, json=j0, status_code=500
        )  # mocking the http response within this context
        response = elucidate.items_by_body_source(
            elucidate="https://elucidate.example.org",
            topic="https://omeka.example.org/topic/virtual:person/matter",
        )
        assert isinstance(response, types.GeneratorType)
        assert next(response) is None


def test_parent_from_annotation():
    d1 = {
        "id": "https://elucidate.example.org/annotation/w3c/foo/bar",
        "type": "Annotation",
        "body": [
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": {
            "type": "SpecificResource",
            "creator": "https://montague.example.org/",
            "dcterms:isPartOf": {
                "id": "http://example.org/manifest/foo/manifest.json",
                "type": "sc:Manifest",
            },
            "generator": "https://montague.example.org/",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://example.org/manifest/foo/canvas/274",
        },
        "motivation": "tagging",
    }
    manifest = elucidate.parent_from_annotation(content=d1)
    assert manifest == "http://example.org/manifest/foo/manifest.json"
    d2 = {
        "id": "https://elucidate.example.org/annotation/w3c/foo/bar",
        "type": "Annotation",
        "body": [
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": {
            "type": "SpecificResource",
            "creator": "https://montague.example.org/",
            "dcterms:isPartOf": "http://example.org/manifest/foo/manifest.json",
            "generator": "https://montague.example.org/",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://example.org/manifest/foo/canvas/274",
        },
        "motivation": "tagging",
    }
    manifest = elucidate.parent_from_annotation(content=d2)
    assert manifest == "http://example.org/manifest/foo/manifest.json"
    d3 = {
        "id": "https://elucidate.example.org/annotation/w3c/foo/bar",
        "type": "Annotation",
        "body": [
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": [
            {
                "type": "SpecificResource",
                "creator": "https://montague.example.org/",
                "dcterms:isPartOf": {
                    "id": "http://example.org/manifest/foo/manifest.json",
                    "type": "sc:Manifest",
                },
                "generator": "https://montague.example.org/",
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": "xywh=659,1646,174,62",
                },
                "source": "http://example.org/manifest/foo/canvas/274",
            },
            {
                "type": "SpecificResource",
                "creator": "https://montague.example.org/",
                "dcterms:isPartOf": {
                    "id": "http://example.org/manifest/foo/manifest.json",
                    "type": "sc:Manifest",
                },
                "generator": "https://montague.example.org/",
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": "xywh=659,1000,184,82",
                },
                "source": "http://example.org/manifest/foo/canvas/274",
            },
        ],
        "motivation": "tagging",
    }
    manifest = elucidate.parent_from_annotation(content=d3)
    assert manifest == "http://example.org/manifest/foo/manifest.json"
    d4 = {
        "id": "https://elucidate.example.org/annotation/w3c/foo/bar",
        "type": "Annotation",
        "body": [
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": "http://example.org/manifest/foo/canvas/274#xywh=659,1646,174,62",
        "motivation": "tagging",
    }
    manifest = elucidate.parent_from_annotation(content=d4)
    assert manifest == "http://example.org/manifest/foo/manifest"
    d5 = {
        "id": "https://elucidate.example.org/annotation/w3c/foo/bar",
        "type": "Annotation",
        "body": [
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": {
            "type": "SpecificResource",
            "creator": "https://montague.example.org/",
            "generator": "https://montague.example.org/",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://example.org/manifest/foo/canvas/274",
        },
        "motivation": "tagging",
    }
    manifest = elucidate.parent_from_annotation(content=d5)
    assert manifest is None  # not a manifest, but code has no way to know


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_topic_page.json"),
    os.path.join(FIXTURE_DIR, "single_topic_page0.json"),
)
def test_manifest_by_topic(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_topic_page.json"), "r") as f:
            j = json.load(f)
        with open(os.path.join(path, "single_topic_page0.json"), "r") as f:
            j0 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.register_uri(
            "GET", url, json=j
        )  # mocking the http response within this context
        mock.register_uri(
            "GET", url2, json=j0
        )  # mocking the http response within this context
        response = elucidate.parents_by_topic(
            elucidate="https://elucidate.example.org",
            topic="https://omeka.example.org/topic/virtual:person/matter",
        )
        manifest_list = list(response)
        assert isinstance(response, types.GeneratorType)
        assert len(manifest_list) == 23
        assert len(list(set(list(manifest_list)))) == 1
        assert manifest_list[0] == "http://waylon.example.org/work/AVT"


def test_uri_contract():
    assert (
        elucidate.uri_contract("https://example.org/foo#XYWH=0,0,200,200")
        == "https://example.org/foo"
    )
    assert elucidate.uri_contract(None) is None


def test_identify_target():
    j = {
        "id": (
            "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        ),
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": {
            "type": "SpecificResource",
            "creator": "https://montague.example.org/",
            "dcterms:isPartOf": {
                "id": "http://waylon.example.org/work/AVT",
                "type": "sc:Manifest",
            },
            "generator": "https://montague.example.org/",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://waylon.example.org/work/AVT/canvas/274",
        },
        "motivation": "tagging",
    }
    assert (
        elucidate.identify_target(j) == "http://waylon.example.org/work/AVT/canvas/274"
    )
    j = {
        "id": (
            "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        ),
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "motivation": "tagging",
    }
    assert (
        elucidate.identify_target(j) == "http://waylon.example.org/work/AVT/canvas/274"
    )
    j = {
        "id": (
            "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        ),
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": [
            {
                "type": "SpecificResource",
                "creator": "https://montague.example.org/",
                "dcterms:isPartOf": {
                    "id": "http://waylon.example.org/work/AVT",
                    "type": "sc:Manifest",
                },
                "generator": "https://montague.example.org/",
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": "xywh=659,1646,174,62",
                },
                "source": "http://waylon.example.org/work/AVT/canvas/274",
            },
            {
                "type": "SpecificResource",
                "creator": "https://montague.example.org/",
                "dcterms:isPartOf": {
                    "id": "http://waylon.example.org/work/AVT",
                    "type": "sc:Manifest",
                },
                "generator": "https://montague.example.org/",
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": "xywh=69,166,104,162",
                },
                "source": "http://waylon.example.org/work/AVT/canvas/274",
            },
        ],
        "motivation": "tagging",
    }
    assert (
        elucidate.identify_target(j) == "http://waylon.example.org/work/AVT/canvas/274"
    )
    j = {
        "id": (
            "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        ),
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "motivation": "tagging",
    }
    assert elucidate.identify_target(j) is None
    j = {
        "id": (
            "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        ),
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            }
        ],
        "target": ("foo", "bar"),
        "motivation": "tagging",
    }
    assert elucidate.identify_target(j) is None


def test_search_by_target():
    s = elucidate.gen_search_by_target_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="w3c",
        field=None,
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/w3c/services/search/target?fields="
        + "source,id&value=https://www.example.org/foo&strict=True"
    )


def test_search_by_target_field():
    s = elucidate.gen_search_by_target_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="w3c",
        field="id",
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/w3c/services/search/target?fields="
        + "id&value=https://www.example.org/foo&strict=True"
    )


def test_search_by_target_field_oa():
    s = elucidate.gen_search_by_target_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="oa",
        field="id",
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/oa/services/search/target?fields="
        + "id&value=https://www.example.org/foo&strict=True"
    )


def test_search_by_target_field_list():
    s = elucidate.gen_search_by_target_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="oa",
        field=["foo", "bar"],
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/oa/services/search/target?fields="
        + "foo,bar&value=https://www.example.org/foo&strict=True"
    )


def test_search_by_target_field_dict():
    s = elucidate.gen_search_by_target_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="w3c",
        field={"foo": "bar"},
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/w3c/services/search/target?fields="
        + "source,id&value=https://www.example.org/foo&strict=True"
    )


def test_search_by_target_field_none():
    s = elucidate.gen_search_by_target_uri(
        target_uri=None,
        elucidate_base="https://elucidate.example.org",
        model="w3c",
        field={"foo": "bar"},
    )
    assert s is None


def test_search_by_container():
    s = elucidate.gen_search_by_container_uri(
        target_uri="https://www.example.org/foo",
        elucidate_base="https://elucidate.example.org",
        model="w3c",
    )
    assert (
        s
        == "https://elucidate.example.org/annotation/w3c/6a88457d6a00b19931cea2fbb3312c2e/"
    )


def test_search_by_container_none():
    s = elucidate.gen_search_by_container_uri(
        target_uri=None, elucidate_base="https://elucidate.example.org", model="w3c"
    )
    assert s is None


def test_item_ids():
    foo = {
        "id": "https://elucidate.example.org/annotation/w3c/10fdd4a621b5625f30abe8fa5c81dbd7/0005ebfd-53ed-499a-930b-62ed96ae73a5",
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "SpecificResource",
                "format": "application/html",
                "creator": "https://montague.example.org/",
                "generator": "https://montague.example.org//nlp/",
                "purpose": "tagging",
                "source": "https://omeka.example.org/topic/virtual:person/matter",
            },
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            },
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            },
        ],
        "target": {
            "type": "SpecificResource",
            "creator": "https://montague.example.org/",
            "dcterms:isPartOf": {
                "id": "http://waylon.example.org/work/AVT",
                "type": "sc:Manifest",
            },
            "generator": "https://montague.example.org/",
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=1225,439,159,67",
            },
            "source": "http://waylon.example.org/work/AVT/canvas/93",
        },
        "motivation": "tagging",
    }
    ids = list(elucidate.item_ids(foo))
    assert ids == [
        "https://elucidate.example.org/annotation/w3c/10fdd4a621b5625f30abe8fa5c81dbd7/0005ebfd-53ed-499a-930b-62ed96ae73a5"
    ]


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_get_anno(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_anno.json"), "r") as f:
            j = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/"
            + "fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        )
        mock.register_uri(
            "GET", url, json=j, headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}
        )
        a, b = elucidate.read_anno(anno_uri=url)
        assert a == j
        assert b == "92d446c4402486f44b98c360c030b672"
        # adapter.register_uri('GET', 'mock://test.com/2', text='Not Found', status_code=404)


def test_get_anno_404():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/"
            + "fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        )
        mock.register_uri("GET", url, text="Not Found", status_code=404)
        a, b = elucidate.read_anno(anno_uri=url)
        assert a is None
        assert b is None


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_topic_page.json"),
    os.path.join(FIXTURE_DIR, "single_topic_page0.json"),
)
def test_get_items(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_topic_page.json"), "r") as f:
            j = json.load(f)
        with open(os.path.join(path, "single_topic_page0.json"), "r") as f:
            j0 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.register_uri(
            "GET", url, json=j
        )  # mocking the http response within this context
        mock.register_uri(
            "GET", url2, json=j0
        )  # mocking the http response within this context
        response = elucidate.get_items(uri=url)
        items = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(items) == 23
        assert (
            items[3]["id"]
            == "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
            + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
        )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_topic_page.json"),
    os.path.join(FIXTURE_DIR, "single_topic_page0.json"),
)
def test_get_items_second(datafiles):
    path = str(datafiles)
    with requests_mock.Mocker() as mock:
        with open(os.path.join(path, "single_topic_page.json"), "r") as f:
            j = json.load(f)
        with open(os.path.join(path, "single_topic_page0.json"), "r") as f:
            j0 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.register_uri(
            "GET", url, json=j
        )  # mocking the http response within this context
        mock.register_uri(
            "GET", url2, json=j0
        )  # mocking the http response within this context
        response = elucidate.get_items(uri=url2)
        items = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(items) == 23


def test_get_items_404():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        mock.register_uri("GET", url, text="Not Found", status_code=404)
        response = elucidate.get_items(uri=url)
        assert list(response) == []


def test_get_items_first_empty():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        j = {"id": url, "first": {"foo": []}}
        mock.register_uri("GET", url, json=j)
        response = elucidate.get_items(uri=url)
        assert list(response) == []


def test_get_items_not_first_empty():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        j = {"id": url, "items": []}
        mock.register_uri("GET", url, json=j)
        response = elucidate.get_items(uri=url)
        assert list(response) == []


def test_get_items_not_first_no_items():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        j = {"id": url, "foo": []}
        mock.register_uri("GET", url, json=j)
        response = elucidate.get_items(uri=url)
        assert list(response) == []


def test_get_items_first_as():
    with requests_mock.Mocker() as mock:
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id,source&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        j = {"id": url, "first": {"as:items": {"@list": [{"id": "foo"}]}}}
        mock.register_uri("GET", url, json=j)
        response = elucidate.get_items(uri=url)
        assert list(response) == [{"id": "foo"}]


def test_create_container():
    with requests_mock.Mocker() as mock:
        name = "foo"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        label = "bar"
        url = elucidate_uri + name + "/"
        mock.register_uri("GET", url, status_code=404)
        mock.register_uri("POST", elucidate_uri, status_code=201)
        assert (
            elucidate.create_container(
                container_name=name, elucidate_uri=elucidate_uri, label=label
            )
            == 201
        )


def test_create_container_exists():
    with requests_mock.Mocker() as mock:
        name = "foo"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        label = "bar"
        url = elucidate_uri + name + "/"
        mock.register_uri("GET", url, status_code=200)
        mock.register_uri("POST", elucidate_uri, status_code=201)
        assert (
            elucidate.create_container(
                container_name=name, elucidate_uri=elucidate_uri, label=label
            )
            == 200
        )


def test_create_container_error():
    with requests_mock.Mocker() as mock:
        name = "foo"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        label = "bar"
        url = elucidate_uri + name + "/"
        mock.register_uri("GET", url, status_code=404)
        mock.register_uri("POST", elucidate_uri, status_code=500)
        assert (
            elucidate.create_container(
                container_name=name, elucidate_uri=elucidate_uri, label=label
            )
            == 500
        )


def test_create_anno_no_elucidate():
    assert elucidate.create_anno(elucidate_base="", annotation={"id": "foo"}) == 400


def test_create_anno():
    with requests_mock.Mocker() as mock:
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        container = "foo/"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        mock.register_uri("GET", elucidate_uri + container, status_code=200)
        mock.register_uri("POST", elucidate_uri + "foo", status_code=201)
        assert (
            elucidate.create_anno(
                elucidate_base="https://elucidate.example.org",
                model="w3c",
                container="foo",
                annotation=j1,
                target="http://waylon.example.org/work/AVT/canvas/274",
            )
            == 201
        )


def test_create_anno_no_container():
    with requests_mock.Mocker() as mock:
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        container = "foo/"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        mock.register_uri("GET", elucidate_uri + container, status_code=404)
        mock.register_uri("POST", elucidate_uri, status_code=404)
        mock.register_uri("POST", elucidate_uri + "foo")
        assert (
            elucidate.create_anno(
                elucidate_base="https://elucidate.example.org",
                model="w3c",
                container="foo",
                annotation=j1,
                target="http://waylon.example.org/work/AVT/canvas/274",
            )
            == 404
        )


def test_create_anno_no_post():
    with requests_mock.Mocker() as mock:
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        container = "foo/"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        mock.register_uri("GET", elucidate_uri + container, status_code=200)
        mock.register_uri("POST", elucidate_uri + "foo", status_code=500)
        assert (
            elucidate.create_anno(
                elucidate_base="https://elucidate.example.org",
                model="w3c",
                container="foo",
                annotation=j1,
                target="http://waylon.example.org/work/AVT/canvas/274",
            )
            == 500
        )


def test_create_anno_no_body():
    with requests_mock.Mocker() as mock:
        container = "foo/"
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        mock.register_uri("GET", elucidate_uri + container, status_code=200)
        mock.register_uri("POST", elucidate_uri + "foo", status_code=201)
        assert (
            elucidate.create_anno(
                elucidate_base="https://elucidate.example.org",
                model="w3c",
                container="foo",
                annotation={},
                target="http://waylon.example.org/work/AVT/canvas/274",
            )
            == 400
        )


def test_create_anno_empty_container():
    with requests_mock.Mocker() as mock:
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        elucidate_uri = "https://elucidate.example.org/annotation/w3c/"
        mock.register_uri("GET", elucidate_uri, status_code=200)
        mock.register_uri(
            "POST",
            "https://elucidate.example.org/annotation/w3c/0c90f6a5254fcc667aa3b068c392aa97/",
            status_code=201,
        )
        mock.register_uri(
            "GET",
            "https://elucidate.example.org/annotation/w3c/0c90f6a5254fcc667aa3b068c392aa97/",
            status_code=200,
        )
        mock.register_uri(
            "POST",
            "https://elucidate.example.org/annotation/w3c/0c90f6a5254fcc667aa3b068c392aa97",
            status_code=201,
        )
        assert (
            elucidate.create_anno(
                elucidate_base="https://elucidate.example.org",
                model="w3c",
                container=None,
                annotation=j1,
                target=None,
            )
            == 201
        )


def test_create_anno_empty_target():
    j1 = {
        "id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": [
            {
                "type": "SpecificResource",
                "format": "application/html",
                "creator": "https://montague.example.org/",
                "generator": "https://montague.example.org//nlp/",
                "purpose": "tagging",
                "source": "https://omeka.example.org/topic/virtual:person/matter",
            },
            {
                "type": "TextualBody",
                "format": "text/plain",
                "creator": "https://montague.example.org/",
                "value": "Matter",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            },
            {
                "creator": "https://montague.example.org/",
                "value": "entity:person",
                "generator": "https://montague.example.org/",
                "purpose": "tagging",
            },
        ],
        "target": "",
        "motivation": "tagging",
    }
    assert (
        elucidate.create_anno(
            elucidate_base="https://elucidate.example.org",
            model="w3c",
            container=None,
            annotation=j1,
            target=None,
        )
        == 400
    )


def test_delete():
    with requests_mock.Mocker() as mock:
        anno_id = "http://foo/bar"
        mock.register_uri(method="DELETE", url=anno_id, status_code=204)
        assert elucidate.delete_anno(anno_uri=anno_id, etag="foo", dry_run=False) == 204


def test_delete_error():
    with requests_mock.Mocker() as mock:
        anno_id = "http://foo/bar"
        mock.register_uri(method="DELETE", url=anno_id, status_code=500)
        assert elucidate.delete_anno(anno_uri=anno_id, etag="foo", dry_run=False) == 500


def test_delete_dry():
    anno_id = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    assert elucidate.delete_anno(anno_uri=anno_id, etag="foo", dry_run=True) == 204


def test_batch_delete():
    with requests_mock.Mocker() as mock:
        elucidate_uri = "https://elucidate.example.org"
        endpoint = elucidate_uri + "/annotation/w3c/services/batch/delete"
        mock.register_uri(method="POST", url=endpoint, status_code=200)
        assert (
            elucidate.batch_delete_target(
                target_uri="https://foo/bar", elucidate_uri=elucidate_uri, dry_run=False
            )
            == 200
        )


def test_batch_delete_error():
    with requests_mock.Mocker() as mock:
        elucidate_uri = "https://elucidate.example.org"
        endpoint = elucidate_uri + "/annotation/w3c/services/batch/delete"
        mock.register_uri(method="POST", url=endpoint, status_code=500)
        assert (
            elucidate.batch_delete_target(
                target_uri="https://foo/bar", elucidate_uri=elucidate_uri, dry_run=False
            )
            == 500
        )


def test_batch_delete_dry():
    elucidate_uri = "https://elucidate.example.org"
    assert (
        elucidate.batch_delete_target(
            target_uri="https://foo/bar", elucidate_uri=elucidate_uri, dry_run=True
        )
        == 200
    )


def test_iterative_delete_by_target_dryrun():
    with requests_mock.Mocker() as mock:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        t = "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,"
            + "id&value=http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        mock.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="search",
                dryrun=True,
            )
            is True
        )


def test_iterative_delete_by_target():
    with requests_mock.Mocker() as mock:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,"
            + "id&value=http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        mock.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="search",
                dryrun=False,
            )
            is True
        )


def test_iterative_delete_by_target_error():
    with requests_mock.Mocker() as mock:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        t = "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,"
            + "id&value=http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        mock.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=500,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="search",
                dryrun=False,
            )
            is False
        )


def test_iterative_delete_by_target_error_method():
    with requests_mock.Mocker() as mock:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        t = "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,"
            + "id&value=http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        mock.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=500,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="foo",
                dryrun=False,
            )
            is False
        )


def test_iterative_delete_by_target_container():
    with requests_mock.Mocker() as mock:
        with open("container.json", "r") as f:
            container = json.load(f)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        mock.register_uri("GET", url=u, json=container)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=500,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="container",
                dryrun=True,
            )
            is True
        )


def test_iterative_delete_by_target_empty_container():
    with requests_mock.Mocker() as mock:
        with open("container_empty.json", "r") as f:
            container = json.load(f)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        mock.register_uri("GET", url=u, json=container)
        assert (
            elucidate.iterative_delete_by_target(
                target=t,
                elucidate_base="https://elucidate.example.org",
                search_method="container",
                dryrun=True,
            )
            is True
        )


def test_batch_update_topics_dry_run():
    n = "https://omeka.example.org/topics/person/new"
    o = ["https://omeka.example.org/topics/person/old"]
    b = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "body": [
            {
                "id": "https://omeka.example.org/topics/person/old",
                "oa:isReplacedBy": "https://omeka.example.org/topics/person/new",
                "source": {
                    "id": "https://omeka.example.org/topics/person/old",
                    "oa:isReplacedBy": "https://omeka.example.org/topics/person/new",
                },
            }
        ],
    }
    result_code, result_body = elucidate.batch_update_body(
        new_topic_id=n,
        old_topic_ids=o,
        elucidate_base="https://elucidate.example.org",
        dry_run=True,
    )
    assert result_body == json.dumps(b)
    assert result_code == 200


def test_batch_update_topics():
    with requests_mock.Mocker() as mock:
        e = "https://elucidate.example.org"
        mock.register_uri(
            "POST", url=e + "/annotation/w3c/services/batch/update", status_code=200
        )
        n = "https://omeka.example.org/topics/person/new"
        o = ["https://omeka.example.org/topics/person/old"]
        result_code, result_body = elucidate.batch_update_body(
            new_topic_id=n, old_topic_ids=o, elucidate_base=e, dry_run=False
        )
        assert result_code == 200


def test_batch_update_topics_error():
    with requests_mock.Mocker() as mock:
        e = "https://elucidate.example.org"
        mock.register_uri(
            "POST", url=e + "/annotation/w3c/services/batch/update", status_code=500
        )
        n = "https://omeka.example.org/topics/person/new"
        o = ["https://omeka.example.org/topics/person/old"]
        result_code, result_body = elucidate.batch_update_body(
            new_topic_id=n, old_topic_ids=o, elucidate_base=e, dry_run=False
        )
        assert result_code == 500


def test_iterative_delete_by_manifest_dry():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture.json", "r") as f:
            m = json.load(f)
        with open("search_by_target.json", "r") as f1:
            j = json.load(f1)
        uri0 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json&strict=True"
        )
        uri1 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json&strict=True"
        )
        uri2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c2.json&strict=True"
        )
        mock.register_uri("GET", url=m["@id"], json=m)
        mock.register_uri("GET", url=uri0, json=j)
        mock.register_uri("GET", url=uri1, json=j)
        mock.register_uri("GET", url=uri2, json=j)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            # mock.register_uri(
            #     "DELETE",
            #     url=anno_uri,
            #     status_code=204,
            #     headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
            #     json={"id": anno_uri},
            # )
        status = elucidate.iiif_iterative_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is True


def test_iterative_delete_by_manifest():
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture.json", "r") as f:
            m = json.load(f)
        with open("search_by_target.json", "r") as f1:
            j = json.load(f1)
        uri0 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json&strict=True"
        )
        uri1 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json&strict=True"
        )
        uri2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c2.json&strict=True"
        )
        mock.register_uri("GET", url=m["@id"], json=m)
        mock.register_uri("GET", url=uri0, json=j)
        mock.register_uri("GET", url=uri1, json=j)
        mock.register_uri("GET", url=uri2, json=j)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            mock.register_uri(
                "DELETE",
                url=anno_uri,
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
        status = elucidate.iiif_iterative_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=False,
        )
        assert status is True


def test_iterative_delete_by_manifest_no_sequence():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_sequence.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        status = elucidate.iiif_iterative_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_iterative_delete_by_manifest_no_canvases():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_canvases.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        status = elucidate.iiif_iterative_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_iterative_delete_by_manifest_404():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        mock.register_uri(
            "GET",
            url="http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json",
            status_code=404,
        )
        status = elucidate.iiif_iterative_delete_by_manifest(
            manifest_uri="http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json",
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_batch_delete_by_manifest_dry():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture.json", "r") as f:
            m = json.load(f)
        with open("search_by_target.json", "r") as f1:
            j = json.load(f1)
        uri0 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json&strict=True"
        )
        uri1 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json&strict=True"
        )
        uri2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c2.json&strict=True"
        )
        mock.register_uri("GET", url=m["@id"], json=m)
        mock.register_uri("GET", url=uri0, json=j)
        mock.register_uri("GET", url=uri1, json=j)
        mock.register_uri("GET", url=uri2, json=j)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/8fe4d33b-1d40-4af8-8390-3b79ac03a46b",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/88293a03-431e-4a2e-8521-5b6fe45ca5e6",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/f7a16ced-5004-4395-9272-ae9678efb108",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/30cebc09-5fd5-4fa5-8c9c-ac55145aa6e1",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/79567dd1-cf86-4393-b556-b8f6892a86bc",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/25065fab-94fc-4a75-b2bb-5f0b01aaa590",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/274105bd-2431-4b85-89b2-38a4855f76e9",
            "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/408d9a20-d188-429d-9223-ca0a8ac1bf8d",
        ]
        for anno_uri in anno_uris:
            mock.register_uri(
                "GET",
                url=anno_uri,
                status_code=200,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno_uri},
            )
            # mock.register_uri(
            #     "DELETE",
            #     url=anno_uri,
            #     status_code=204,
            #     headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
            #     json={"id": anno_uri},
            # )
        status = elucidate.iiif_batch_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is True


def test_batch_delete_by_manifest_no_sequence():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_sequence.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        status = elucidate.iiif_batch_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_batch_delete_by_manifest_no_canvases():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_canvases.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        status = elucidate.iiif_batch_delete_by_manifest(
            manifest_uri=m["@id"],
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_batch_delete_by_manifest_404():
    """
    Uses existing test JSON
    :return:
    """
    with requests_mock.Mocker() as mock:
        mock.register_uri(
            "GET",
            url="http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json",
            status_code=404,
        )
        status = elucidate.iiif_batch_delete_by_manifest(
            manifest_uri="http://iiif.io/api/presentation/2.0/example/fixtures/19/manifest.json",
            elucidate_uri="https://elucidate.example.org",
            dry_run=True,
        )
        assert status is False


def test_batch_delete_topic_dry_run():
    o = "https://omeka.example.org/topics/person/old"
    b = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "body": {
            "id": "https://omeka.example.org/topics/person/old",
            "source": {"id": "https://omeka.example.org/topics/person/old"},
        },
    }
    result_code, result_body = elucidate.batch_delete_topic(
        topic_id=o, elucidate_base="https://elucidate.example.org", dry_run=True
    )
    assert result_body == json.dumps(b)
    assert result_code == 200


def test_batch_delete_topic():
    with requests_mock.Mocker() as mock:
        e = "https://elucidate.example.org"
        mock.register_uri(
            "POST", url=e + "/annotation/w3c/services/batch/delete", status_code=200
        )
        o = "https://omeka.example.org/topics/person/old"
        result_code, result_body = elucidate.batch_delete_topic(
            topic_id=o, elucidate_base=e, dry_run=False
        )
        b = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "body": {
                "id": "https://omeka.example.org/topics/person/old",
                "source": {"id": "https://omeka.example.org/topics/person/old"},
            },
        }
        assert result_body == json.dumps(b)
        assert result_code == 200


def test_batch_delete_topic_error():
    with requests_mock.Mocker() as mock:
        e = "https://elucidate.example.org"
        b = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "body": {
                "id": "https://omeka.example.org/topics/person/old",
                "source": {"id": "https://omeka.example.org/topics/person/old"},
            },
        }
        mock.register_uri(
            "POST", url=e + "/annotation/w3c/services/batch/delete", status_code=500
        )
        o = "https://omeka.example.org/topics/person/old"
        result_code, result_body = elucidate.batch_delete_topic(
            topic_id=o, elucidate_base=e, dry_run=False
        )
        assert result_body == json.dumps(b)
        assert result_code == 500
