from pyelucidate import pyelucidate as elucidate
import json
import pytest
import os


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def test_remove_keys():
    test_data = {"bar": "thing", "notbar": "nothing"}
    assert elucidate.remove_keys(test_data, ["bar"]) == {"notbar": "nothing"}


def test_target_extract_source():
    test_data = {
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
    }
    assert (
        elucidate.target_extract(json_dict=test_data, fake_selector=False)
        == "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62"
    )


def test_target_extract_source_fake():
    test_data = {
        "type": "SpecificResource",
        "creator": "https://montague.example.org/",
        "dcterms:isPartOf": {
            "id": "http://waylon.example.org/work/AVT",
            "type": "sc:Manifest",
        },
        "generator": "https://montague.example.org/",
        "source": "http://waylon.example.org/work/AVT/canvas/274",
    }
    assert (
        elucidate.target_extract(json_dict=test_data, fake_selector=True)
        == "http://waylon.example.org/work/AVT/canvas/274#xywh=0,0,50,50"
    )


def test_target_extract_source_no_fake():
    test_data = {
        "type": "SpecificResource",
        "creator": "https://montague.example.org/",
        "dcterms:isPartOf": {
            "id": "http://waylon.example.org/work/AVT",
            "type": "sc:Manifest",
        },
        "generator": "https://montague.example.org/",
        "source": "http://waylon.example.org/work/AVT/canvas/274",
    }
    assert (
        elucidate.target_extract(json_dict=test_data, fake_selector=False)
        == "http://waylon.example.org/work/AVT/canvas/274"
    )


def test_format_results():
    annos = [{"foo": "bar"}, {"a": "b"}]
    result = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@id": "http://annotations.example.org/foo",
        "@type": "sc:AnnotationList",
        "resources": [{"foo": "bar"}, {"a": "b"}],
    }
    assert (
        elucidate.format_results(
            annotation_list=annos, request_uri="http://annotations.example.org/foo"
        )
        == result
    )


def test_format_results_empty():
    assert (
        elucidate.format_results(
            annotation_list=None, request_uri="http://annotations.example.org/foo"
        )
        is None
    )


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_mirador_oa(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    result = {"chars": chars, "format": "application/html"}
    assert elucidate.mirador_oa(j["body"][0]) == result


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_mirador_oa_val(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    result = {"@type": "oa:Tag", "chars": "Matter"}
    assert elucidate.mirador_oa(j["body"][1]) == result


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_transformation(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno.json")
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    with open(test_data, "r") as f:
        j = json.load(f)
    i = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": i,
        "@type": "oa:Annotation",
        "resource": [
            {"chars": chars, "format": "application/html"},
            {"@type": "oa:Tag", "chars": "Matter"},
            {"@type": "oa:Tag", "chars": "entity:person"},
        ],
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_transformation_flatten(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    j["creator"] = {"@id": "https://montague.example.org/"}
    i = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": i,
        "@type": "oa:Annotation",
        "resource": [
            {"chars": chars, "format": "application/html"},
            {"@type": "oa:Tag", "chars": "Matter"},
            {"@type": "oa:Tag", "chars": "entity:person"},
        ],
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno.json"))
def test_transformation_no_transform(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    assert elucidate.transform_annotation(item=j) == j


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "single_anno_single_body.json"))
def test_transformation_single_body(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno_single_body.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    i = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": i,
        "@type": "oa:Annotation",
        "resource": {"chars": chars, "format": "application/html"},
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "single_anno_single_body_multi_target.json")
)
def test_transformation_single_body_multi_target(datafiles):
    path = str(datafiles)
    test_data = os.path.join(path, "single_anno_single_body_multi_target.json")
    with open(test_data, "r") as f:
        j = json.load(f)
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    i = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": i,
        "@type": "oa:Annotation",
        "resource": {"chars": chars, "format": "application/html"},
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


def test_transformation_single_body_simple_target():
    i = (
        "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/"
        + "8cbec70c-e859-4624-b1e3-1bbec5bcca85"
    )
    j = {
        "id": i,
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": {
            "type": "SpecificResource",
            "format": "application/html",
            "creator": "https://montague.example.org/",
            "generator": "https://montague.example.org//nlp/",
            "purpose": "tagging",
            "source": "https://omeka.example.org/topic/virtual:person/matter",
        },
        "target": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "motivation": "tagging",
    }
    chars = (
        '<a href="https://omeka.example.org/topic/virtual:person/matter">'
        + "https://omeka.example.org/topic/virtual:person/matter</a>"
    )
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": i,
        "@type": "oa:Annotation",
        "resource": {"chars": chars, "format": "application/html"},
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )
