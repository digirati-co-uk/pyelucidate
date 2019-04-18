import json
from typing import Optional, Tuple, Union, Callable
from urllib.parse import quote_plus, urlparse, urlunparse, urlencode, parse_qsl, parse_qs
import asyncio
import hashlib
import logging
import aiohttp
import requests
from aiohttp import ClientSession, TCPConnector
from copy import deepcopy


def set_query_field(url: str, field: str, value: Union[int, str], replace: bool = False):
    """
    Parse out the different parts of a URL, and optionally replace a query string parameter,
    before return the unparsed new URL.

    :param url: URL to parse
    :param field: field where the value should be replaced
    :param value: replacement value
    :param replace: boolean, if True, replace query string parameter
    :return: unparsed URL
    """
    components = urlparse(url)
    query_pairs = parse_qsl(urlparse(url).query)

    if replace:  # create list of field/value tuples, excluding the field to replaced
        query_pairs = [(f, v) for (f, v) in query_pairs if f != field]
    query_pairs.append((field, value))  # append the new field/value tuple

    new_query_str = urlencode(query_pairs)  # url encode the query parameters

    # Construct the new URL
    new_components = (
        components.scheme,
        components.netloc,
        components.path,
        components.params,
        new_query_str,
        components.fragment,
    )
    return urlunparse(new_components)  # return the urlunparsed URL


def annotation_pages(result: Optional[dict]) -> Optional[str]:
    """
    Generator which yields URLs for annotation pages from an Activity Streams paged result set.
    Works by looking for the "last" page in the paged result set and incrementing between 0 and
    last.

    Does not request each page and examine "next" or "previous".

    For example, given an Activity Streams paged result set which contains:

    .. code-block:: json

        {"last": "https://elucidate.example.org/annotation/w3c/services/search/body?page=3&fields
        =source&value=FOO&desc=1"}


    Will yield:

    https://elucidate.example.org/annotation/w3c/services/search/body?fields=source&value=FOO&desc=1&page=0

    https://elucidate.example.org/annotation/w3c/services/search/body?fields=source&value=FOO&desc=1&page=1

    https://elucidate.example.org/annotation/w3c/services/search/body?fields=source&value=FOO&desc=1&page=2

    https://elucidate.example.org/annotation/w3c/services/search/body?fields=source&value=FOO&desc=1&page=3


    :param result: Activity Streams paged result set
    :return: Activity Streams page URIs.
    """
    if result:
        if result["total"] > 0:
            last = urlparse(result["last"])
            last_page = parse_qs(last.query)["page"][0]
            for p in range(0, int(last_page) + 1):
                page = set_query_field(result["last"], field="page", value=p, replace=True)
                yield page
        else:
            return
    else:
        return


def items_by_body_source(elucidate: str, topic: str, strict: bool = True) -> dict:
    """
    Generator to yield annotations from query to Elucidate by body source.

    For example, for a W3C web annotation, with body:

    .. code-block:: json

      {"body": [
                {
                  "type": "SpecificResource",
                  "format": "application/html",
                  "creator": "https://montague.example.org/",
                  "generator": "https://montague.example.org//nlp/",
                  "purpose": "tagging",
                  "source": "https://www.example.org/themes/foo"
                }
            ]}

    This function will query Elucidate for all annotations with body id or body source ==
    "https://www.example.org/themes/foo".

    If strict = False, this would match both:

        https://www.example.org/themes/foo

    and

        https://www.example.org/themes/foobar

    If strict = True, only annotations with an exact match on the body source will be returned.

    :param elucidate: URL for Elucidate server, e.g. https://elucidate.example.org
    :param topic:  URI for body source, e.g. https://www.example.org/themes/foo
    :param strict: if strict, use strict = True.
    :return: annotation dict
    """
    t = quote_plus(topic)
    search_uri = "".join(
        [
            elucidate,
            "/annotation/w3c/services/search/body?fields=id,",
            "source&value=",
            t,
            "&strict=" + str(strict),
        ]
    )
    r = requests.get(search_uri)
    if r.status_code == requests.codes.ok:
        for page in annotation_pages(r.json()):
            items = requests.get(page).json()["items"]
            for item in items:
                yield item
    else:
        logging.warning("%s returned %s", search_uri, r.status_code)
        yield


def parent_from_annotation(content: dict) -> Optional[str]:
    """
    Parse W3C web annotation and attempt to yield URI for parent object
    the annotation target is part of.

    A typical use would be to return the parent IIIF Presentation API manifest URI
    for an annotation on a IIIF Presentation API canvas or fragment of a canvas.

    The code makes the assumption that, if passed a string for target, rather than an object,
    that manifest and canvas URI patterns follow the model used by the RESTful DLCS API model.

    On this pattern, a canvas with URI:

        https://example.org/iiif/foo/canvas/c1

    will have a parent manifest with URI:

        https://example.org/iiif/foo/manifest

    This assumption may not, and probably will not, hold for other sources.

    If the annotation has a "dcterms:isPartOf" field within the target, the value of
    "dcterms:isPartOf" will be returned. If there are a list of annotation targets, the first
    parent will be returned.

    :param content: annotation object
    :return: target parent URI
    """
    if isinstance(content["target"], str):
        # derives the manifest URI from the canvas URI
        # only works for specific RESTful DLCS URI pattern
        parent = content["target"].split("canvas")[0] + "manifest"
    else:
        # just use the first target if it's a list of targets.
        if isinstance(content["target"], list):
            t = content["target"][0]
        else:
            t = content["target"]
        try:  # if a string, return the string
            if isinstance(t["dcterms:isPartOf"], str):
                parent = t["dcterms:isPartOf"]
            else:  # else return the id
                parent = t["dcterms:isPartOf"]["id"]
        except KeyError:
            # annotations with no dcterms:isPartOf
            return
    return parent


def parents_by_topic(elucidate: str, topic: str) -> Optional[str]:
    """
    Generator parses results from an Elucidate topic search request, and yields parent/manifest
    URIs.

    The code makes the assumption that, if passed a string for target, rather than an object,
    that manifest and canvas URI patterns follow the model used by the RESTful DLCS API model.

    On this pattern, a canvas with URI:

        https://example.org/iiif/foo/canvas/c1

    will have a parent manifest with URI:

        https://example.org/iiif/foo/manifest

    This assumption may not, and probably will not, hold for other sources.

    :param elucidate: URL for Elucidate server, e.g. https://elucidate.example.org
    :param topic:  URL for body source, e.g. https://topics.example.org/people/mary+jones
    :return: manifest URI
    """
    if topic:
        for count, anno in enumerate(items_by_body_source(elucidate, topic, strict=True)):
            m = parent_from_annotation(anno)
            if m:
                yield m


def batch_update_body(
    new_topic_id: str, old_topic_ids: list, elucidate_base: str, dry_run: bool = True
) -> Tuple[int, dict]:
    """
    Use Elucidate's bulk update APIs to replace all instances of each of a list of body source or
    id URIs (aka a topic) with the new URI (aka topic).

    https://github.com/dlcs/elucidate-server/blob/master/USAGE.md#batch-update

    :param new_topic_id: topic ids to use, string
    :param old_topic_ids: topic ids to replace, list
    :param elucidate_base: elucidate base URI, e.g. https://elucidate.example.org
    :param dry_run: if True, will simply log JSON and URI and then return a 200
    :return: POST status code
    """
    bodies = []
    for old_topic_id in old_topic_ids:
        bodies.append(
            {
                "id": old_topic_id,
                "oa:isReplacedBy": new_topic_id,
                "source": {"id": old_topic_id, "oa:isReplacedBy": new_topic_id},
            }
        )
    post_data = json.dumps({"@context": "http://www.w3.org/ns/anno.jsonld", "body": bodies})
    post_uri = elucidate_base + "/annotation/w3c/services/batch/update"
    logging.debug("Posting %s to %s", post_data, post_uri)
    if not dry_run:
        resp = requests.post(
            url=post_uri,
            data=post_data,
            headers={
                "Content-type": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"'
            },
        )
        if resp.status_code != requests.codes.OK:
            logging.error("%s returned %s", post_uri, resp.content)
        return resp.status_code, post_data
    else:
        logging.debug("Dry run.")
        return 200, post_data


def batch_delete_topic(topic_id: str, elucidate_base: str, dry_run: bool = True) -> Tuple[int, str]:
    """
    Use Elucidate's batch update apis to delete all instances of a topic URI.

    https://github.com/dlcs/elucidate-server/blob/master/USAGE.md#batch-delete

    :param topic_id: topic id to delete
    :param elucidate_base: elucidate base URI, e.g. https://elucidate.example.org
    :param dry_run: if True, will simply log and then return a 200
    :return: tuple - http POST status code, JSON POSTed (as string)
    """
    post_uri = elucidate_base + "/annotation/w3c/services/batch/delete"
    post_data = json.dumps(
        {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "body": {"id": topic_id, "source": {"id": topic_id}},
        }
    )
    logging.debug("Posting %s to %s", post_data, post_uri)
    if not dry_run:
        resp = requests.post(
            url=post_uri,
            data=post_data,
            headers={
                "Content-type": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"'
            },
        )
        if resp.status_code != requests.codes.OK:
            logging.error("%s returned %s", post_uri, resp.content)
        return resp.status_code, post_data
    else:
        logging.debug("Dry run.")
        return 200, post_data


def gen_search_by_target_uri(
    target_uri: Optional[str], elucidate_base: str, model: str = "w3c", field=None
) -> Optional[str]:
    """
    Returns a search URI for searching Elucidate for a target using Elucidate's basic search API.

    This URI can be passed to other functions to return the result of the query.

    :param model: oa or w3c, defaults to w3c.
    :param elucidate_base: base URI for the annotation server, e.g. https://elucidate.example.org
    :param target_uri: target URI to search for, e.g. a IIIF Presentatiion API canvas or manifest
    URI
    :param field: list of fields to search on, defaults to both source and id
    :return: uri
    """
    if field is None:
        field = ["source", "id"]
    else:
        if isinstance(field, str):  # catch strings
            field = [field]
        elif isinstance(field, list):
            field = field
        else:  # just use the default.
            field = ["source", "id"]
    if elucidate_base and target_uri:
        uri = "".join(
            [
                "/".join([elucidate_base, "annotation", model, "services/search/target?fields="]),
                ",".join(field),
                "&value=",
                target_uri,
                "&strict=True",
            ]
        )
        return uri
    else:
        return None


def gen_search_by_container_uri(
    elucidate_base: str, target_uri: Optional[str], model: str = "w3c"
) -> Optional[str]:
    """
    Return the annotation container uri for a target. Assumes that the container URI
    is an md5 hash of the target URI (as per current DLCS general practice).

    This URI can be passed to other functions to return the result of the query.

    :param elucidate_base:  base URI for the annotation server, e.g. https://elucidate.example.org
    :param target_uri: target URI to search for, e.g. IIIF Presentation API manifest or canvas URI
    :param model: oa or w3c
    :return: uri
    """
    if elucidate_base and target_uri:
        container = hashlib.md5(target_uri.encode("utf-8")).hexdigest()
        uri = "/".join([elucidate_base, "annotation", model, container, ""])
        return uri
    else:
        return None


def get_items(uri: str) -> Optional[dict]:
    """
    Page through an ActivityStreams paged result set, yielding
    each page's items one at a time.

    :param uri: Request URI, e.g. provided by gen_search_by_target_uri()
    :return: item
    """
    while True:
        page_response = requests.get(uri)
        if page_response.status_code != 200:  # end of no results
            return
        j = page_response.json()
        if "first" in j:  # first page of result set
            if "as:items" in j["first"]:
                items = j["first"]["as:items"]["@list"]
            elif "items" in j["first"]:
                items = j["first"]["items"]
            else:
                items = None
        else:  # not first page of result set
            try:
                items = j["items"]
            except KeyError:
                items = None
        if items:
            for item in items:
                yield item
        try:  # try to get the next page (on first page)
            uri = j["first"]["next"]
        except KeyError:  # try to get the next page (on non-first page)
            uri = j.get("next")
        if uri is None:  # no next page, so end
            break


def item_ids(item: dict) -> Optional[str]:
    """
    Small helper function to yield identifier URI(s) for item from an Activity Streams item.
    Will yield both '@id' and 'id' values.


    :param item: Item from an activity streams page
    :return: uri
    """
    for i in ["@id", "id"]:
        if i in item:
            uri = item[i]
            yield uri


def read_anno(anno_uri: str) -> (Optional[str], Optional[str]):
    """
    GET an annotation from Elucidate, returns a tuple of annotation content and ETag

    :param anno_uri: URI for annotation
    :return: annotation content, etag
    """
    r = requests.get(anno_uri)
    if r.status_code == requests.codes.ok:
        anno = r.json()
        etag = r.headers["ETag"].replace('W/"', "").replace('"', "")  # cleanup weak ETag format for
        # reuse
        return anno, etag
    else:
        return None, None


def delete_anno(anno_uri: str, etag: str, dry_run: bool = True) -> int:
    """
    Delete an individual annotation, requires etag.

    Optionally, can be run as a dry run which will not delete the annotation.

    :param anno_uri: URI for annotation
    :param etag: ETag
    :param dry_run: if True, log and return a 204
    :return: return DELETE request status code
    """
    header_dict = {
        "If-Match": etag,
        "Accept": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
        "Content-Type": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
    }
    if not dry_run:
        r = requests.delete(anno_uri, headers=header_dict)
        if r.status_code == 204:
            logging.info("Deleted %s", anno_uri)
        else:
            logging.error("Failed to delete %s server returned %s", anno_uri, r.status_code)
        return r.status_code
    else:  # log and return a 204
        logging.debug("Dry run")
        return 204


def create_container(container_name: str, label: str, elucidate_uri: str) -> int:
    """
    Create an annotation container with a container name and label.

    :param container_name: name of the container
    :param label:  label for the container
    :param elucidate_uri:  uri for the annotation server, including full path, e.g.
        https://elucidate.example.org/annotation/w3c/
    :return: POST request status code
    """
    container_headers = {
        "Slug": container_name,
        "Content-Type": "application/ld+json",
        "Accept": 'application/ld+json;profile="http://www.w3.org/ns/anno.jsonld"',
    }
    container_dict = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "AnnotationCollection",
        "label": label,
    }
    container_body = json.dumps(container_dict)
    container_uri = elucidate_uri + container_name + "/"
    c_get = requests.get(container_uri)
    if c_get.status_code == 200:
        logging.debug("Container already exists at: %s", container_uri)
        return c_get.status_code
    else:
        r = requests.post(elucidate_uri, headers=container_headers, data=container_body)
        if r.status_code in [200, 201]:
            logging.debug("Container created at: %s", container_uri)
        else:
            logging.error(
                "Could not create container at: %s reason: %s", container_uri, r.status_code
            )
        return r.status_code


def uri_contract(uri: str) -> Optional[str]:
    """
    Contract a URI to just the schema, netloc, and path

    For example, for:

        https://example.org/foo#XYWH=0,0,200,200

    return:

        https://example.org/foo

    :param uri: URI to contract
    :return: contracted URI
    """
    if uri:
        parsed = urlparse(uri)
        contracted = urlunparse((parsed[0], parsed[1], parsed[2], None, None, None))
        return contracted
    else:
        return None


def identify_target(annotation_content: dict) -> Optional[str]:
    """
    Identify the base level target for an annotation, for

        https://example.org/foo#XYWH=0,0,200,200

    output

        https://example.org/foo

    If the annotation has multiple targets, return just base level target for the first.

    :param annotation_content: annotation dict
    :return: uri
    """
    targets = []
    if "target" in annotation_content:
        if isinstance(annotation_content["target"], str):
            target = uri_contract(annotation_content["target"])
            return target
        elif isinstance(annotation_content["target"], dict):
            targets = list(
                set(
                    [
                        uri_contract(v)
                        for k, v in annotation_content["target"].items()
                        if k in ["id", "@id", "source"]
                    ]
                )
            )
            if targets:
                return targets[0]
        elif isinstance(annotation_content["target"], list):
            targets = []
            for t in annotation_content["target"]:
                targets.extend(
                    list(
                        set([uri_contract(v) for k, v in t.items() if k in ["id", "@id", "source"]])
                    )
                )
        if targets:
            return targets[0]
        else:
            return None
    else:
        return None


def create_anno(
    elucidate_base: str,
    annotation: dict,
    target: Optional[str] = None,
    container: Optional[str] = None,
    model: Optional[str] = "w3c",
) -> Tuple[int, Optional[str]]:
    """
    POST an annotation to Elucidate, can be optionally passed a container, if container is None
    will use the MD5 hash of the manifest or canvas target URI as the container name.

    If no @context is provided, the code will insert the appropriate context based on the model.

    :param elucidate_base: base URI for the annotation server, e.g. https://elucidate.example.org
    :param target: target for the annotation (optional), will attempt to parse anno for target
            if not present
    :param annotation: annotation object
    :param container: container name (optional), will use hash of target uri if not present
    :param model: oa or w3c
    :return: status code from Elucidate, annotation id (or none)
    """
    if elucidate_base:
        if annotation:
            # N.B. assumes all targets in the annotation have the same base URI
            if not container:
                if not target:
                    target = identify_target(annotation)
                    print("Target", target)
                    if not target:
                        logging.error("Could not identify a target to hash for the container")
                        return 400, None
                container = hashlib.md5(target.encode("utf-8")).hexdigest()
            elucidate = "/".join([elucidate_base, "annotation", model, ""])
            container_status = create_container(
                container_name=container, elucidate_uri=elucidate, label=target
            )
            if container_status in [200, 201]:
                anno_headers = {
                    "Content-Type": "application/ld+json",
                    "Accept": 'application/ld+json;profile="http://www.w3.org/ns/anno.jsonld"',
                }
                post_uri = "/".join([elucidate_base, "annotation", model, container, ""])
                if not hasattr(annotation, "@context"):
                    if model == "w3c":
                        annotation["@context"] = "http://www.w3.org/ns/anno.jsonld"
                    elif model == "oa":
                        annotation["@context"] = "https://www.w3.org/ns/oa.jsonld"
                anno_body = json.dumps(annotation, indent=4, sort_keys=True)
                r = requests.post(post_uri, headers=anno_headers, data=anno_body)
                if r.status_code in [200, 201]:
                    logging.debug("POST annotation at %s", post_uri)
                    j = r.json()
                    return r.status_code, j.get("id")
                else:
                    logging.error("Could not POST annotation at %s", post_uri)
                return r.status_code, None
            else:
                logging.error("No annotation container found")
                return 404, None
        else:
            logging.error("No annotation body was provided")
            return 400, None
    else:
        logging.error("No Elucidate URI was provided")
        return 400, None


def update_anno(anno_uri: str, anno_content: dict, etag: str, dry_run: bool = True) -> int:
    """
    Update an individual annotation, requires etag.

    Optionally, can be run as a dry run which will not update the annotation but will return a 200.

    :param anno_uri: URI for annotation
    :param anno_content: the annotation content
    :param etag: ETag
    :param dry_run: if True, log and return a 200
    :return: return PUT request status code
    """
    header_dict = {
        "If-Match": etag,
        "Accept": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
        "Content-Type": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
    }
    if not dry_run:
        r = requests.put(url=anno_uri, data=json.dumps(anno_content), headers=header_dict)
        if r.status_code == 200:
            logging.info("Update %s", anno_uri)
        else:
            logging.error("Failed to update %s server returned %s", anno_uri, r.status_code)
        return r.status_code
    else:  # log and return a 200
        logging.debug("Dry run")
        return 200


def batch_delete_target(target_uri: str, elucidate_uri: str, dry_run: bool = True) -> int:
    """
    Use Elucidate's batch delete API to delete everything with a given target id or target source
    URI.

    https://github.com/dlcs/elucidate-server/blob/master/USAGE.md#batch-delete

    :param target_uri: URI to delete
    :param elucidate_uri: URI of the Elucidate server, e.g. https://elucidate.example.org
    :param dry_run: if True, do not actually delete, just log request and return a 200
    :return: status code
    """
    header_dict = {
        "Accept": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
        "Content-Type": 'application/ld+json; profile="http://www.w3.org/ns/anno.jsonld"',
    }
    delete_dict = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "target": {"id": target_uri, "source": {"id": target_uri}},
    }
    logging.debug(json.dumps(delete_dict, indent=4))
    uri = elucidate_uri + "/annotation/w3c/services/batch/delete"
    if not dry_run:
        r = requests.post(uri, data=json.dumps(delete_dict), headers=header_dict)
        logging.info("Bulk delete target: %s", target_uri)
        logging.info("Bulk delete status: %s", r.status_code)
        if r.status_code != requests.codes.ok:
            logging.warning(r.content)
        return r.status_code
    else:
        return 200


def iterative_delete_by_target(
    target: str, elucidate_base: str, search_method: str = "container", dryrun: bool = True
) -> bool:
    """
    Delete all annotations in a container for a target URI. Works by querying for the
    annotations and then iteratively deleting them one at a time.

    Note, that this is _not_ an operation using Elucidate's batch delete APIs.

    Negative: could be slow, and involve many consecutive HTTP requests

    Positive: as the code is handling the annotations one at a time, it will not time out
    with very large result sets.

    The function can build the list of annotations to delete using either:

        the Elucidate search by target API,

        or a hash of the target URI to get a container URI.

    N.B. choosing the container method assumes that container ID as an MD5 hash of the target URI.


    :param dryrun: if True, will not actually delete, just logs and returns True (for success)
    :param search_method: 'container' (hash of target URI) or 'search' (Elucidate query by target)
    :param target: target URI
    :param elucidate_base: base URI for Elucidate, e.g. https://elucidate.example.org
    :return: boolean success or fail, True if no errors on _any_ request.
    """
    statuses = []
    if search_method == "container":
        uri = gen_search_by_container_uri(elucidate_base=elucidate_base, target_uri=target)
    elif search_method == "search":
        uri = gen_search_by_target_uri(target_uri=target, elucidate_base=elucidate_base)
    else:
        uri = None
    if uri:
        anno_items = get_items(uri)
        annotations = []
        for item in anno_items:
            annotations.extend([i for i in item_ids(item)])
        anno_uris = list(set(annotations))
        if anno_uris:
            for annotation in anno_uris:
                content, etag = read_anno(annotation)
                s = delete_anno(content["id"], etag, dry_run=dryrun)
                statuses.append(s)
                logging.info("Deleting %s status %s, dry run: %s", content["id"], s, dryrun)
        else:
            logging.warning("No annotations for %s", uri)
            return True
    else:
        logging.error("Could not generate an Elucidate query for %s", target)
        return False
    if statuses and all([x == 204 for x in statuses]):
        logging.info("Successfully deleted all annotations for target %s", target)
        return True
    else:
        logging.error("Could not delete all annotations for target %s", target)
        return False


def iiif_iterative_delete_by_manifest(
    manifest_uri: str, elucidate_uri: str, method: str = "search", dry_run: bool = True
) -> bool:
    """
    Provides a IIIF aware wrapper around the iterative_delete_by_target function.

    Iteratively delete all annotations for every canvas in a IIIF Presentation manifest and for the
    IIIF Presentation API manifest itself.

    Requests annotations either by container or by target URI and iteratively deletes the
    annotations by id, one at a time, using HTTP DELETE.

    Does not use Elucidate's batch delete APIs.

    :param dry_run: if True, will not actually delete
    :param method: identify the annotations to delete via container (hash) or search (Elucidate
    query)
    :param manifest_uri: URI for IIIF Presentation API manifest.
    :param elucidate_uri: Elucidate base URI, e.g. https://elucidate.example.org
    :return: boolean success or fail
    """
    statuses = []
    r = requests.get(manifest_uri)
    if r.status_code == requests.codes.ok:
        manifest = r.json()
        if "sequences" in manifest:
            if "canvases" in manifest["sequences"][0]:
                canvases = manifest["sequences"][0]["canvases"]
                canvas_ids = [c["@id"] for c in canvases]
                for canvas in canvas_ids:
                    statuses.append(
                        iterative_delete_by_target(
                            elucidate_base=elucidate_uri,
                            target=canvas,
                            search_method=method,
                            dryrun=dry_run,
                        )
                    )
            else:
                logging.error("Could not find canvases in manifest %s", manifest_uri)
                return False
        else:
            logging.error("Manifest %s contained no sequences", manifest_uri)
            return False
        statuses.append(
            iterative_delete_by_target(
                elucidate_base=elucidate_uri,
                target=manifest["@id"],
                search_method=method,
                dryrun=dry_run,
            )
        )
    else:
        logging.error("Could not GET manifest %s", manifest_uri)
        return False
    return all(statuses)


def iiif_batch_delete_by_manifest(
    manifest_uri: str, elucidate_uri: str, dry_run: bool = True
) -> bool:
    """
    Provides a IIIF aware wrapper around the _batch_delete_by_target_ function. Requests a IIIF
    Presentation API manifest and deletes all of the annotations with the canvas or the manifest
    URIs as their target.

    Use Elucidate's batch delete API to delete everything with a given target id or target source
    URI.

    https://github.com/dlcs/elucidate-server/blob/master/USAGE.md#batch-delete

    :param manifest_uri: URI of IIIF Presentation API manifest (must be de-referenceable)
    :param elucidate_uri: base URI for Elucidate, e.g. https://elucidate.example.org
    :param dry_run: if True, will not actually delete the content
    :return: boolean for status, True if no errors, False if error on any delete operation.
    """
    statuses = []
    r = requests.get(manifest_uri)
    if r.status_code == requests.codes.ok:
        manifest = r.json()
        if "sequences" in manifest:
            if "canvases" in manifest["sequences"][0]:
                canvases = manifest["sequences"][0]["canvases"]
                canvas_ids = [c["@id"] for c in canvases]
                for canvas in canvas_ids:
                    statuses.append(
                        200
                        == batch_delete_target(
                            target_uri=canvas, elucidate_uri=elucidate_uri, dry_run=dry_run
                        )
                    )
            else:
                logging.error("Manifest %s contained no canvases", manifest_uri)
                return False
        else:
            logging.error("Manifest %s contained no sequences", manifest_uri)
            return False
        statuses.append(
            200
            == batch_delete_target(
                target_uri=manifest_uri, elucidate_uri=elucidate_uri, dry_run=dry_run
            )
        )
    else:
        logging.error("Could not GET manifest %s", manifest_uri)
        return False
    return all(statuses)


def remove_keys(d: dict, keys: list) -> dict:
    """
    Remove keys from a dictionary.

    :param d: dict to edit
    :param keys: list of keys to remove
    :return: dict with keys removed
    """
    return {k: v for k, v in d.items() if k in (set(d.keys()) - set(keys))}


def target_extract(json_dict: dict, fake_selector: bool = False) -> Optional[str]:
    """
    Extract the target and turn into a simple 'on'.

    Optionally, fake a selector, e.g. for whole canvas annotations, generate a target XYWH bounding
    box at top left.

    :param fake_selector: if True, create a top left 50px box and associate with that.
    :param json_dict: annotation content as dictionary
    :return: string for the target URI
    """
    if "source" in json_dict:
        if "selector" in json_dict:
            return "#".join([json_dict["source"], json_dict["selector"]["value"]])
        else:
            if fake_selector:
                return "#".join([json_dict["source"], "xywh=0,0,50,50"])
            else:
                return json_dict["source"]


def transform_annotation(
    item: dict, flatten_at_ids: bool = True, transform_function: Optional[Callable] = None
) -> Optional[dict]:
    """
    Transform an annotation given an arbitrary
    function that is passed in.

    For example, W3C to OA using "mirador_oa".

    The function will remove keys not used in the Open Annotation model.

    If no transform_function is provided the annotation will be returned unaltered.

    :param item: annotation
    :param flatten_at_ids: if True replace @id dict with simple "@id" : "foo"
    :param transform_function: function to pass the annotation through
    :return:
    """
    item_copy = deepcopy(item)
    if transform_function:
        if flatten_at_ids:  # flatten dicts with @ids to simple key / value
            for k, v in item_copy.items():
                if "@id" in item_copy[k]:
                    item_copy[k] = item_copy[k]["@id"]
        item_copy["motivation"] = "oa:tagging"  # force motivation to tagging
        if item_copy.get("body"):
            if isinstance(item_copy["body"], list):  # transform each anno body (in list of bodies)
                item_copy["body"] = [transform_function(body) for body in item_copy["body"]]
            elif isinstance(item_copy["body"], dict):  # transform single anno (if not a list)
                item_copy["body"] = transform_function(item_copy["body"])
        if isinstance(item_copy["target"], dict):  # replace the target with a simple 'on'
            item_copy["on"] = target_extract(item_copy["target"])  # o
        elif isinstance(item_copy["target"], list):
            item_copy["on"] = [target_extract(o) for o in item_copy["target"]][0]  # o_list[0]
        else:
            item_copy["on"] = item_copy["target"]
        item_copy["@id"] = item_copy["id"]
        item_copy["@type"] = "oa:Annotation"
        item_copy["resource"] = item_copy.get("body")
        item_copy = remove_keys(
            d=item_copy, keys=["generator", "label", "target", "creator", "type", "id", "body"]
        )  # remove unused keys
        return item_copy
    else:
        return item


def mirador_oa(w3c_body: dict) -> dict:
    """
    Transform a single W3C Web Annotation Body (e.g. as produced by Montague) and returns
    formatted for Open Annotation in the  Mirador client.

    :param w3c_body: annotation body
    :return: transformed annotation body
    """
    new_body = {}
    if "source" in w3c_body.keys():
        new_body["chars"] = '<a href="' + w3c_body["source"] + '">' + w3c_body["source"] + "</a>"
        new_body["format"] = "application/html"
    if "value" in w3c_body.keys():
        new_body["@type"] = "oa:Tag"
        new_body["chars"] = w3c_body["value"]
    new_body = remove_keys(new_body, ["value", "type", "generator", "source", "purpose"])
    return new_body


def format_results(annotation_list: Optional[list], request_uri: str) -> Optional[dict]:
    """
    Takes a list of annotations and returns as a standard Presentation API
    Annotation List.

    :param annotation_list: list of annotations
    :param request_uri: the URI to use for the @id
    :return dict or None
    """
    if annotation_list:
        anno_list = {
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@type": "sc:AnnotationList",
            "@id": request_uri,
            "resources": annotation_list,
        }
        return anno_list
    else:
        return


async def fetch_all(urls: list, connector_limit: int = 5) -> asyncio.Future:
    """
    Launch async requests for all web pages in list of urls.


    :param urls: list of URLs to fetch
    :param connector_limit: integer for max parallel connections
    :return results from requests


    """
    tasks = []
    fetch.start_time = dict()  # dictionary of start times for each url
    async with ClientSession(connector=TCPConnector(limit=connector_limit)) as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task)  # create list of tasks
        results = await asyncio.gather(*tasks)  # gather task responses
        return results


async def fetch(url: str, session: aiohttp.client.ClientSession) -> dict:
    """
    Asynchronously fetch a url, using specified ClientSession.

    """
    async with session.get(url) as response:
        resp = await response.json()
        return resp


def async_items_by_topic(elucidate: str, topic: str, **kwargs) -> dict:
    """
    Asynchronously yield annotations from a query by topic to Elucidate.

    Does an asynchronous get for all the annotations, and then yields the annotations with
    optional transformation provided by the "trans_function" arg.

    :param elucidate: Elucidate server, e.g. https://elucidate.example.org
    :param topic: URI from body source, e.g. 'https://topics.example.org/people/mary+jones'
    :return: annotation object
    """
    t = quote_plus(topic)
    sample_uri = elucidate + "/annotation/w3c/services/search/body?fields=source,id&value=" + t
    r = requests.get(sample_uri)
    if r.status_code == requests.codes.ok:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(
            fetch_all([p for p in annotation_pages(r.json())])
        )  # tasks to do
        pages = loop.run_until_complete(future)  # loop until done
        for page in pages:
            for item in page["items"]:
                yield transform_annotation(
                    item=item,
                    flatten_at_ids=kwargs.get("flatten_ids"),
                    transform_function=kwargs.get("trans_function"),
                )


def async_items_by_target(elucidate: str, target_uri: str, **kwargs) -> dict:
    """
    Asynchronously yield annotations from a query by topic to Elucidate.

    Async requests all of the annotation pages before yielding.

    :param elucidate: Elucidate server, e.g. https://elucidate.example.org
    :param target_uri: URI from target source and id, e.g. 'https://manifest.example.org/manifest/1'
    :return: annotation object
    """
    t = quote_plus(target_uri)
    sample_uri = elucidate + "/annotation/w3c/services/search/target?fields=source,id&value=" + t
    r = requests.get(sample_uri)
    filter_by = kwargs.get("filter_by")
    if r.status_code == requests.codes.ok:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(
            fetch_all([p for p in annotation_pages(r.json())])
        )  # tasks to do
        pages = loop.run_until_complete(future)  # loop until done
        for page in pages:
            if page.get("items"):
                for item in page["items"]:
                    # will not return if the annotation doesn't have the
                    # filter property, e.g. {"creator": ["id": "https://example.org/users/foo"]}
                    # if the value of they is a simple string, e.g. if the annotation has
                    # "creator" : ""https://example.org/users/foo"
                    # the code will ignore the "id" key, and check that all values match,
                    # irresepctive of
                    # the key.
                    if filter_by:
                        for filter_key, filter_value_list in filter_by.items():
                            for filter_value in filter_value_list:
                                if item.get(filter_key):
                                    if isinstance(item.get(filter_key), dict):
                                        if all(
                                            [
                                                item[filter_key][k] == v
                                                for k, v in filter_value.items()
                                            ]
                                        ):
                                            yield transform_annotation(
                                                item=item,
                                                flatten_at_ids=kwargs.get("flatten_ids"),
                                                transform_function=kwargs.get("trans_function"),
                                            )
                                    elif isinstance(item.get(filter_key), str):
                                        if all(
                                            [item[filter_key] == v for k, v in filter_value.items()]
                                        ):
                                            yield transform_annotation(
                                                item=item,
                                                flatten_at_ids=kwargs.get("flatten_ids"),
                                                transform_function=kwargs.get("trans_function"),
                                            )

                    else:
                        yield transform_annotation(
                            item=item,
                            flatten_at_ids=kwargs.get("flatten_ids"),
                            transform_function=kwargs.get("trans_function"),
                        )


def async_items_by_container(
    elucidate: str,
    container: Optional[str] = None,
    target_uri: Optional[str] = None,
    header_dict: Optional[dict] = None,
    **kwargs
) -> Optional[dict]:
    """
    Asynchronously yield annotations from a query by container to Elucidate.

    Container can be hashed from target URI, or provided

    :param elucidate: Elucidate server, e.g. https://elucidate.example.org
    :param target_uri: URI from target source and id, e.g. 'https://manifest.example.org/manifest/1'
    :param container: container path
    :param header_dict: dict of headers
    :return: annotation object
    """
    if target_uri and not container:
        container = hashlib.md5(target_uri.encode("utf-8")).hexdigest()
    if container:
        if not container.endswith("/"):
            container += "/"
        sample_uri = elucidate + "/annotation/w3c/" + container
        r = requests.get(sample_uri, headers=header_dict)
        filter_by = kwargs.get("filter_by")
        if r.status_code == requests.codes.ok:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            future = asyncio.ensure_future(
                fetch_all([p for p in annotation_pages(r.json())])
            )  # tasks to do
            pages = loop.run_until_complete(future)  # loop until done
            for page in pages:
                if page.get("items"):
                    for item in page["items"]:
                        if filter_by:
                            for filter_key, filter_value_list in filter_by.items():
                                for filter_value in filter_value_list:
                                    if item.get(filter_key):
                                        if isinstance(item.get(filter_key), dict):
                                            if all(
                                                [
                                                    item[filter_key][k] == v
                                                    for k, v in filter_value.items()
                                                ]
                                            ):
                                                yield transform_annotation(
                                                    item=item,
                                                    flatten_at_ids=kwargs.get("flatten_ids"),
                                                    transform_function=kwargs.get("trans_function"),
                                                )
                                        elif isinstance(item.get(filter_key), str):
                                            if all(
                                                [
                                                    item[filter_key] == v
                                                    for k, v in filter_value.items()
                                                ]
                                            ):
                                                yield transform_annotation(
                                                    item=item,
                                                    flatten_at_ids=kwargs.get("flatten_ids"),
                                                    transform_function=kwargs.get("trans_function"),
                                                )

                        else:
                            yield transform_annotation(
                                item=item,
                                flatten_at_ids=kwargs.get("flatten_ids"),
                                transform_function=kwargs.get("trans_function"),
                            )
    else:
        return


def async_manifests_by_topic(elucidate: str, topic: Optional[str] = None) -> Optional[list]:
    """
    Asynchronously fetch the results from a topic query to Elucidate and yield manifest URIs

    N.B. assumption, if passed a string for target, rather than an object,
    that manifest and canvas URI patterns follow old API DLCS/Presley model.

    :param elucidate: URL for Elucidate server, e.g. https://elucidate.example.org
    :param topic:  URL for body source, e.g. https://topics.example.org/people/mary+jones
    :return: manifest URI
    """
    if topic:
        return list(
            set([parent_from_annotation(anno) for anno in async_items_by_topic(elucidate, topic)])
        )


def iterative_delete_by_target_async_get(
    target: str, elucidate_base: str, dryrun: bool = True
) -> bool:
    """
    Delete all annotations in a container for a target uri. Works by querying for the
    annotations and then iteratively deleting them one at a time. Not a bulk delete operation
    using Elucidate's bulk APIs.

    N.B. Negative: could be slow, and involve many HTTP requests, Positive: doesn't really matter
    how big the result set is, it won't time out, as handling the annotations one at a time.

    Asynchronous query using the Elucidate search by target API to fetch the list of annotations to
    delete.

    DELETE is not asychronous, but sequential.

    :param dryrun: if True, will not actually delete, just logs and returns True (for success)
    :param target: target uri
    :param elucidate_base: base URI for Elucidate, e.g. https://elucidate.example.org
    :return: boolean success or fail, True if no errors on _any_ request.
    """
    statuses = []
    anno_items = async_items_by_target(elucidate=elucidate_base, target_uri=target)
    annotations = []
    for item in anno_items:
        annotations.extend([i for i in item_ids(item)])
    anno_uris = list(set(annotations))
    if anno_uris:
        for annotation in anno_uris:
            content, etag = read_anno(annotation)
            s = delete_anno(content["id"], etag, dry_run=dryrun)
            statuses.append(s)
            logging.info("Deleting %s status %s, dry run: %s", content["id"], s, dryrun)
    else:
        logging.warning("No annotations for %s", target)
        return True

    if statuses and all([x == 204 for x in statuses]):
        logging.info("Successfully deleted all annotations for target %s", target)
        return True
    else:
        logging.error("Could not delete all annotations for target %s", target)
        return False


def iiif_iterative_delete_by_manifest_async_get(
    manifest_uri: str, elucidate_uri: str, dry_run: bool = True
) -> bool:
    """
    Delete all annotations for every canvas in a IIIF manifest and for the manifest.

    Uses asynchronous code to parallel get the search results to build the annotation list.

    N.B. does NOT do an async DELETE. Delete is sequential.

    :param dry_run: if True, will not actually delete, just prints URIs
    :param manifest_uri: uri for IIIF manifest
    :param elucidate_uri: Elucidate base uri
    :return: boolean success or fail
    """
    statuses = []
    if manifest_uri:
        r = requests.get(manifest_uri)
        if r.status_code == requests.codes.ok:
            manifest = r.json()
            if "sequences" in manifest:
                if "canvases" in manifest["sequences"][0]:
                    canvases = manifest["sequences"][0]["canvases"]
                    canvas_ids = [c["@id"] for c in canvases]
                    for canvas in canvas_ids:
                        statuses.append(
                            iterative_delete_by_target_async_get(
                                elucidate_base=elucidate_uri, target=canvas, dryrun=dry_run
                            )
                        )
                else:
                    logging.error("Could not find canvases in manifest %s", manifest_uri)
                    return False
            else:
                logging.error("Manifest %s contained no sequences", manifest_uri)
                return False
            statuses.append(
                iterative_delete_by_target_async_get(
                    elucidate_base=elucidate_uri, target=manifest["@id"], dryrun=dry_run
                )
            )
        else:
            logging.error("Could not GET manifest %s", manifest_uri)
            return False
    return all(statuses)


def async_items_by_creator(elucidate: str, creator_id: str, **kwargs) -> dict:
    """
    Asynchronously yield annotations from a query by creator to Elucidate.

    Async requests all of the annotation pages before yielding.

    :param elucidate: Elucidate server, e.g. https://elucidate.example.org
    :param creator_id: URI from target source and id, e.g. 'https://manifest.example.org/manifest/1'
    :return: annotation object
    """
    c = quote_plus(creator_id)
    sample_uri = (
        elucidate
        + "/annotation/w3c/services/search/creator?type=id&levels=annotation&strict=True&value="
        + c
    )
    r = requests.get(sample_uri)
    filter_by = kwargs.get("filter_by")
    if r.status_code == requests.codes.ok:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.ensure_future(
            fetch_all([p for p in annotation_pages(r.json())])
        )  # tasks to do
        pages = loop.run_until_complete(future)  # loop until done
        for page in pages:
            if page.get("items"):
                for item in page["items"]:
                    # will not return if the annotation doesn't have the
                    # filter property, e.g. {"motivation": [{"id": "bookmarking"}]}
                    # if the value of they is a simple string, e.g. if the annotation has
                    # "motivation" : "bookmarking"
                    # the code will ignore the "id" key, and check that all values match,
                    # irresepctive of
                    # the key.
                    if filter_by:
                        for filter_key, filter_value_list in filter_by.items():
                            for filter_value in filter_value_list:
                                if item.get(filter_key):
                                    if isinstance(item.get(filter_key), dict):
                                        if all(
                                            [
                                                item[filter_key][k] == v
                                                for k, v in filter_value.items()
                                            ]
                                        ):
                                            yield transform_annotation(
                                                item=item,
                                                flatten_at_ids=kwargs.get("flatten_ids"),
                                                transform_function=kwargs.get("trans_function"),
                                            )
                                    elif isinstance(item.get(filter_key), str):
                                        if all(
                                            [item[filter_key] == v for k, v in filter_value.items()]
                                        ):
                                            yield transform_annotation(
                                                item=item,
                                                flatten_at_ids=kwargs.get("flatten_ids"),
                                                transform_function=kwargs.get("trans_function"),
                                            )

                    else:
                        yield transform_annotation(
                            item=item,
                            flatten_at_ids=kwargs.get("flatten_ids"),
                            transform_function=kwargs.get("trans_function"),
                        )
