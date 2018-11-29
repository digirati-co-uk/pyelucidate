from pyelucidate import pyelucidate as elucidate
import asyncio
from aioresponses import aioresponses
import json
import types
import requests_mock


def test_fetch_all():
    with aioresponses() as mock:
        mock.get("http://elucidate.example.org", payload=dict(foo="bar"))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(
            elucidate.fetch_all([p for p in ["http://elucidate.example.org"]])
        )  # tasks to do
        results = loop.run_until_complete(future)  # loop until done
        assert results == [{"foo": "bar"}]


def test_items_by_body_source():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("single_topic_page.json", "r") as f:
            j = json.load(f)
        with open("single_topic_page0.json", "r") as f:
            j0 = json.load(f)
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=source,id&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.get(url2, payload=j0)  # mocking the http response within this context
        m.register_uri("GET", url, json=j)  # mocking the http response within this context
        response = elucidate.async_items_by_topic(
            elucidate="https://elucidate.example.org",
            topic="https://omeka.example.org/topic/virtual:person/matter",
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 23
        assert anno_list[3] == j1


def test_items_by_target():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0"
        ]
        for anno_uri in anno_uris:
            mock.get(anno_uri, payload=search_by_target_page)
        response = elucidate.async_items_by_target(
            elucidate="https://elucidate.example.org", target_uri=t
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 8
        assert anno_list[0] == search_by_target_page["items"][0]


def test_items_by_target_filter():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        anno_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0"
        ]
        for anno_uri in anno_uris:
            mock.get(anno_uri, payload=search_by_target_page)
        response = elucidate.async_items_by_target(
            elucidate="https://elucidate.example.org", target_uri=t,
            filter_by={"creator": [{"id": "https://montague.example.org/"}]}
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 8
        assert anno_list[0] == search_by_target_page["items"][0]


def test_items_by_target_container():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("container.json", "r") as f:
            container = json.load(f)
        with open("container_page.json", "r") as f0:
            container_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        u1 = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/?desc=1&page=0"
        m.register_uri("GET", url=u, json=container)
        mock.get(u1, payload=container_page)
        response = elucidate.async_items_by_container(
            elucidate="https://elucidate.example.org", target_uri=t
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 8


def test_items_by_target_container_container():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("container.json", "r") as f:
            container = json.load(f)
        with open("container_page.json", "r") as f0:
            container_page = json.load(f0)
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        u1 = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/?desc=1&page=0"
        m.register_uri("GET", url=u, json=container)
        mock.get(u1, payload=container_page)
        response = elucidate.async_items_by_container(
            elucidate="https://elucidate.example.org", container="6913ae2c2f5a7b6e59bc1d88192be0f6"
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 8


def test_items_by_target_container_filtered():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("container.json", "r") as f:
            container = json.load(f)
        with open("container_page.json", "r") as f0:
            container_page = json.load(f0)
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        u1 = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/?desc=1&page=0"
        m.register_uri("GET", url=u, json=container)
        mock.get(u1, payload=container_page)
        response = elucidate.async_items_by_container(
            elucidate="https://elucidate.example.org", container="6913ae2c2f5a7b6e59bc1d88192be0f6",
            filter_by={"creator": [{"id": "https://montague.example.org/"}]}
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 8


def test_items_by_target_container_filtered_none():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("container.json", "r") as f:
            container = json.load(f)
        with open("container_page.json", "r") as f0:
            container_page = json.load(f0)
        u = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/"
        u1 = "https://elucidate.example.org/annotation/w3c/6913ae2c2f5a7b6e59bc1d88192be0f6/?desc=1&page=0"
        m.register_uri("GET", url=u, json=container)
        mock.get(u1, payload=container_page)
        response = elucidate.async_items_by_container(
            elucidate="https://elucidate.example.org", container="6913ae2c2f5a7b6e59bc1d88192be0f6",
            filter_by={"creator": [{"id": "https://foo.example.org/"}]}
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 0


def test_items_by_target_container_none():
        response = elucidate.async_items_by_container(
            elucidate="https://elucidate.example.org"
        )
        anno_list = list(response)
        assert isinstance(response, types.GeneratorType)  # is True
        assert len(anno_list) == 0


def test_manifests_by_topic():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("single_topic_page.json", "r") as f:
            j = json.load(f)
        with open("single_topic_page0.json", "r") as f:
            j0 = json.load(f)
        with open("single_anno.json", "r") as f:
            j1 = json.load(f)
        url = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=source,id&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter"
        )
        url2 = (
            "https://elucidate.example.org/annotation/w3c/services/search/body?fields=id%2Csource&value="
            + "https%3A%2F%2Fomeka.example.org%2Ftopic%2Fvirtual%3Aperson%2Fmatter&desc=1&page=0"
        )
        mock.get(url2, payload=j0)  # mocking the http response within this context
        m.register_uri("GET", url, json=j)  # mocking the http response within this context
        response = elucidate.async_manifests_by_topic(
            elucidate="https://elucidate.example.org",
            topic="https://omeka.example.org/topic/virtual:person/matter",
        )
        assert isinstance(response, list)  # is True
        assert response == ['http://waylon.example.org/work/AVT']


def test_items_delete_by_target():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        page_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0"
        ]
        for page_uri in page_uris:
            mock.get(page_uri, payload=search_by_target_page)
        for anno in search_by_target_page["items"]:
            m.register_uri("GET", url=anno["id"], headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}, json=anno)
        response = elucidate.iterative_delete_by_target_async_get(
            elucidate_base="https://elucidate.example.org", target=t, dryrun=True
        )
        assert response is True


def test_items_delete_by_target_not_dryrun():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        page_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0"
        ]
        for page_uri in page_uris:
            mock.get(page_uri, payload=search_by_target_page)
        for anno in search_by_target_page["items"]:
            m.register_uri("GET", url=anno["id"], headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}, json=anno)
            m.register_uri(
                "DELETE",
                url=anno["id"],
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno["id"]},
            )
        response = elucidate.iterative_delete_by_target_async_get(
            elucidate_base="https://elucidate.example.org", target=t, dryrun=False
        )
        assert response is True


def test_items_delete_by_target_errors():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        page_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0"
        ]
        for page_uri in page_uris:
            mock.get(page_uri, payload=search_by_target_page)
        for anno in search_by_target_page["items"]:
            m.register_uri("GET", url=anno["id"], headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}, json=anno)
            m.register_uri(
                "DELETE",
                url=anno["id"],
                status_code=500,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno["id"]},
            )
        response = elucidate.iterative_delete_by_target_async_get(
            elucidate_base="https://elucidate.example.org", target=t, dryrun=False
        )
        assert response is False


def test_items_delete_by_target_missing():
    with requests_mock.Mocker() as m:
        t = "http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c10.json"
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc10.json"
        )
        m.register_uri("GET", url=u, status_code=404)

        response = elucidate.iterative_delete_by_target_async_get(
            elucidate_base="https://elucidate.example.org", target=t, dryrun=False
        )
        assert response is True


def test_items_delete_by_manifest_not_dry_run():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        with open("manifest_fixture.json", "r") as f1:
            manifest = json.load(f1)
        man = manifest["@id"]
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        m.register_uri("GET", url=man, json=manifest)
        page_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0",
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value=" +
            "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc2.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?desc=1&fields=source&page=0" +
            "&value=http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value=" +
            "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2F19%2Fmanifest.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?desc=1&fields=source&page=0" +
            "&value=http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        ]
        for page_uri in page_uris:  # just return the same json in each instance (for easier testing)
            mock.get(page_uri, payload=search_by_target_page)
            m.register_uri("GET", url=page_uri, json=search_by_target_page)
        for anno in search_by_target_page["items"]:
            m.register_uri("GET", url=anno["id"], headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}, json=anno)
            m.register_uri(
                "DELETE",
                url=anno["id"],
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno["id"]},
            )
        response = elucidate.iiif_iterative_delete_by_manifest_async_get(
            elucidate_uri="https://elucidate.example.org", manifest_uri=man, dry_run=False
        )
        assert response is True


def test_items_delete_by_manifest_dry_run():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        with open("search_by_target.json", "r") as f:
            search_by_target = json.load(f)
        with open("search_by_target_0.json", "r") as f0:
            search_by_target_page = json.load(f0)
        with open("manifest_fixture.json", "r") as f1:
            manifest = json.load(f1)
        man = manifest["@id"]
        u = (
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc1.json"
        )
        m.register_uri("GET", url=u, json=search_by_target)
        m.register_uri("GET", url=man, json=manifest)
        page_uris = [
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source&value="
            + "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2F"
            + "example%2Ffixtures%2Fcanvas%2F19%2Fc1.json&desc=1&page=0",
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value=" +
            "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2Fcanvas%2F19%2Fc2.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?desc=1&fields=source&page=0" +
            "&value=http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?fields=source,id&value=" +
            "http%3A%2F%2Fiiif.io%2Fapi%2Fpresentation%2F2.0%2Fexample%2Ffixtures%2F19%2Fmanifest.json",
            "https://elucidate.example.org/annotation/w3c/services/search/target?desc=1&fields=source&page=0" +
            "&value=http://iiif.io/api/presentation/2.0/example/fixtures/canvas/19/c1.json"
        ]
        for page_uri in page_uris:  # just return the same json in each instance (for easier testing)
            mock.get(page_uri, payload=search_by_target_page)
            m.register_uri("GET", url=page_uri, json=search_by_target_page)
        for anno in search_by_target_page["items"]:
            m.register_uri("GET", url=anno["id"], headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'}, json=anno)
            m.register_uri(
                "DELETE",
                url=anno["id"],
                status_code=204,
                headers={"ETag": 'W/"92d446c4402486f44b98c360c030b672'},
                json={"id": anno["id"]},
            )
        response = elucidate.iiif_iterative_delete_by_manifest_async_get(
            elucidate_uri="https://elucidate.example.org", manifest_uri=man, dry_run=True
        )
        assert response is True


def test_items_delete_by_manifest_no_manifest():
    with aioresponses() as mock, requests_mock.Mocker() as m:
        man = "https://example.org/foo"
        m.register_uri("GET", url=man, status_code=404)
        response = elucidate.iiif_iterative_delete_by_manifest_async_get(
            elucidate_uri="https://elucidate.example.org", manifest_uri=man, dry_run=True
        )
        assert response is False


def test_items_delete_by_manifest_no_sequence():
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_sequence.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        response = elucidate.iiif_iterative_delete_by_manifest_async_get(
            elucidate_uri="https://elucidate.example.org", manifest_uri=m["@id"], dry_run=True
        )
        assert response is False


def test_items_delete_by_manifest_no_canvases():
    with requests_mock.Mocker() as mock:
        with open("manifest_fixture_no_canvases.json", "r") as f:
            m = json.load(f)
        mock.register_uri("GET", url=m["@id"], json=m)
        response = elucidate.iiif_iterative_delete_by_manifest_async_get(
            elucidate_uri="https://elucidate.example.org", manifest_uri=m["@id"], dry_run=True
        )
        assert response is False
