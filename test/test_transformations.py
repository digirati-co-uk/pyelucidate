from pyelucidate import pyelucidate as elucidate
import json


def test_remove_keys():
    foo = {"bar": "thing", "notbar": "nothing"}
    assert elucidate.remove_keys(foo, ["bar"]) == {"notbar": "nothing"}


def test_target_extract_source():
    foo = {
        "type": "SpecificResource",
        "creator": "https://montague.example.org/",
        "dcterms:isPartOf": {"id": "http://waylon.example.org/work/AVT", "type": "sc:Manifest"},
        "generator": "https://montague.example.org/",
        "selector": {
            "type": "FragmentSelector",
            "conformsTo": "http://www.w3.org/TR/media-frags/",
            "value": "xywh=659,1646,174,62",
        },
        "source": "http://waylon.example.org/work/AVT/canvas/274",
    }
    assert (
        elucidate.target_extract(json_dict=foo, fake_selector=False)
        == "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62"
    )


def test_target_extract_source_fake():
    foo = {
        "type": "SpecificResource",
        "creator": "https://montague.example.org/",
        "dcterms:isPartOf": {"id": "http://waylon.example.org/work/AVT", "type": "sc:Manifest"},
        "generator": "https://montague.example.org/",
        "source": "http://waylon.example.org/work/AVT/canvas/274",
    }
    assert (
        elucidate.target_extract(json_dict=foo, fake_selector=True)
        == "http://waylon.example.org/work/AVT/canvas/274#xywh=0,0,50,50"
    )


def test_target_extract_source_no_fake():
    foo = {
        "type": "SpecificResource",
        "creator": "https://montague.example.org/",
        "dcterms:isPartOf": {"id": "http://waylon.example.org/work/AVT", "type": "sc:Manifest"},
        "generator": "https://montague.example.org/",
        "source": "http://waylon.example.org/work/AVT/canvas/274",
    }
    assert (
        elucidate.target_extract(json_dict=foo, fake_selector=False)
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


def test_mirador_oa():
    with open("single_anno.json", "r") as f:
        j = json.load(f)
    result = {
        "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
        "format": "application/html",
    }
    assert elucidate.mirador_oa(j["body"][0]) == result


def test_mirador_oa_val():
    with open("single_anno.json", "r") as f:
        j = json.load(f)
    result = {"@type": "oa:Tag", "chars": "Matter"}
    assert elucidate.mirador_oa(j["body"][1]) == result


def test_transformation():
    with open("single_anno.json", "r") as f:
        j = json.load(f)
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "@type": "oa:Annotation",
        "resource": [
            {
                "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
                "format": "application/html",
            },
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


def test_transformation_flatten():
    with open("single_anno.json", "r") as f:
        j = json.load(f)
    j["creator"] = {"@id": "https://montague.example.org/"}
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "@type": "oa:Annotation",
        "resource": [
            {
                "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
                "format": "application/html",
            },
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


def test_transformation_no_transform():
    with open("single_anno.json", "r") as f:
        j = json.load(f)
    assert elucidate.transform_annotation(item=j) == j


def test_transformation_single_body():
    with open("single_anno_single_body.json", "r") as f:
        j = json.load(f)
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "@type": "oa:Annotation",
        "resource": {
            "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
            "format": "application/html",
        },
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


def test_transformation_single_body_multi_target():
    with open("single_anno_single_body_multi_target.json", "r") as f:
        j = json.load(f)
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "@type": "oa:Annotation",
        "resource": {
            "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
            "format": "application/html",
        },
    }
    assert (
        elucidate.transform_annotation(
            item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
        )
        == result
    )


def test_transformation_single_body_simple_target():
    j = {
        "id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "type": "Annotation",
        "creator": "https://montague.example.org/",
        "generator": "https://montague.example.org/",
        "body": {
            "type": "SpecificResource",
            "format": "application/html",
            "creator": "https://montague.example.org/",
            "generator": "https://montague.example.org//nlp/",
            "purpose": "tagging",
            "source": "https://omeka.example.org/topic/virtual:person/matter"
        },
        "target": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "motivation": "tagging"
    }
    result = {
        "motivation": "oa:tagging",
        "on": "http://waylon.example.org/work/AVT/canvas/274#xywh=659,1646,174,62",
        "@id": "https://elucidate.example.org/annotation/w3c/fd8c7a22abcde179e30850b5d1f7c439/8cbec70c-e859-4624-b1e3-1bbec5bcca85",
        "@type": "oa:Annotation",
        "resource": {
            "chars": '<a href="https://omeka.example.org/topic/virtual:person/matter">https://omeka.example.org/topic/virtual:person/matter</a>',
            "format": "application/html",
        },
    }
    assert (
            elucidate.transform_annotation(
                item=j, flatten_at_ids=True, transform_function=elucidate.mirador_oa
            )
            == result
    )
