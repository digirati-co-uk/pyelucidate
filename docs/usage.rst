========
Usage
========

To use PyElucidate in a project::

	import pyelucidate


Introduction
============


The _PyElucidate_ library primarily consists of simple functions with no state, which interact with an instance of the
Elucidate server using the `W3C Web Annotation Protocol`__ but also Elucidate's additional service APIs.

See Elucidate's usage_ documentation for further information.

.. _W3CA:  https://www.w3.org/TR/annotation-protocol/
__ W3CA_
.. _usage: https://github.com/dlcs/elucidate-server/blob/master/USAGE.md


Basic W3C Functions
===================


POST a new annotation
---------------------

This code will create the annotation container based on an MD5 hash of the annotation target, if a container slug is not
passed in as a parameter.

The code will insert the appropriate ``@context`` if no ``@context`` is provided.

.. code-block:: python

    from pyelucidate import pyelucidate

    anno = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "body": [{"value": "Foo", "purpose": "tagging"}],
        "target": {
            "type": "SpecificResource",
            "dcterms:isPartOf": {
                "id": "http://example.org/manifest/foo/manifest.json",
                "type": "sc:Manifest",
            },
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://example.org/manifest/foo/canvas/274",
        },
        "motivation": "tagging",
    }

    status_code, anno_id = pyelucidate.create_anno(
        elucidate_base="https://elucidate.example.org", model="w3c", annotation=anno
    )
    assert status_code == 201
    assert anno_id is not None


Post a new annotation to a specified container ("foo"):

.. code-block:: python

    from pyelucidate import pyelucidate
    import requests

    anno = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "body": [{"value": "Foo", "purpose": "tagging"}],
        "target": {
            "type": "SpecificResource",
            "dcterms:isPartOf": {
                "id": "http://example.org/manifest/foo/manifest.json",
                "type": "sc:Manifest",
            },
            "selector": {
                "type": "FragmentSelector",
                "conformsTo": "http://www.w3.org/TR/media-frags/",
                "value": "xywh=659,1646,174,62",
            },
            "source": "http://example.org/manifest/foo/canvas/274",
        },
        "motivation": "tagging",
    }

    status_code, anno_id = pyelucidate.create_anno(
        elucidate_base="https://elucidate.example.org", model="w3c", annotation=anno,
        container="foo"
    )
    container_contents = requests.get("https://elucidate.example.org/foo/")
    assert status_code == 201
    assert anno_id is not None
    assert container_contents.status_code == 200


GET an annotation
-----------------

Will fetch the annotation and return annotation plus the ETag for the annotation.

.. code-block:: python

    from pyelucidate import pyelucidate
    import json

    annotation, etag = pyelucidate.read_anno("https://elucidate.example.org/annotation/w3c"
                              "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")


DELETE an annotation
--------------------

The W3C Web Annotation Protocol requires an ``If-Match`` header with the ETag for the
annotation. This function requires the ETag to be provided.

If ``dry_run`` is ``True`` (the default), the function will return a 204 without deleting the annotation.

The example below shows fetching an annotation, checking the purpose for the body, and deleting the annotation.


.. code-block:: python

    from pyelucidate import pyelucidate

    annotation, etag = pyelucidate.read_anno("https://elucidate.example.org/annotation/w3c"
                              "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")


    if annotation["body"]["purpose"] == "tagging":
        status = pyelucidate.delete_anno(anno_uri = annotation["id"], etag=etag, dry_run=False)
        assert status == 204


CREATE a container
------------------

It is also possible to create a container, before POSTing any annotations.

Note that `elucidate_uri` contains the full path, including the model `w3c`, and not just the base elucidate URI.


.. code-block:: python

    from pyelucidate import pyelucidate


    status_code = pyelucidate.create_container(
        container_name="bar",
        label="A test container",
        elucidate_uri="https://elucidate.example.org/annotation/w3c/",
    )

    assert status_code in [200, 201]


This code will check if the container already exists, before creating, so can be run repeatedly if required.


PUT an updated annotation
-------------------------

The W3C Web Annotation Protocol requires an ``If-Match`` header with the ETag for the
annotation. This function requires the ETag to be provided.

If ``dry_run`` is ``True`` (the default), the function will return a 200 without updating the annotation.

The example below shows fetching an annotation, updating the body, and updating the annotation.


.. code-block:: python

    from pyelucidate import pyelucidate


    annotation, etag = pyelucidate.read_anno("https://elucidate.example.org/annotation/w3c"
                                             "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")

    # Change the annotation body value
    annotation["body"]["value"] = "foo"

    # Put the update annotation
    status_code = pyelucidate.update_anno(anno_uri=annotation["id"], anno_content=annotation, etag=etag, dry_run=False)

    # Check the result
    annotation, etag = pyelucidate.read_anno("https://elucidate.example.org/annotation/w3c"
                                             "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")
    assert annotation["body"]["value"] == "foo"


Elucidate Services
==================

Elucidate provides a number of additional services which extend the W3C Web Annotation Protocol.


Query by body source
--------------------

Query Elucidate for all annotations with a specified body source.

Typical usage:

    For tagging annotations, where the target is tagged with a particular topic URI, return all annotations
    that have been tagged with that topic URI.

For example, to find all annotations, tagged with `https://omeka.example.org/topic/virtual:person/mary+smith`:


.. code-block:: python

    from pyelucidate import pyelucidate


    annotations = pyelucidate.items_by_body_source(elucidate="http://elucidate.example.org",
                                                   strict=True,
                                                   topic="https://omeka.example.org/topic/virtual:person/mary+smith")

    # identifiers for annotations with body source
    anno_ids = [a["id"] for a in annotations]


This function is a generator that yields the annotations.

The `strict` parameter sets whether Elucidate does a prefix style search or looks for an exact match.

Query by target
---------------

Query Elucidate for all annotations with a specified target.

Typical usage:

    For a IIIF canvas, return all annotations with that canvas as target.


PyElucidate provides a single asynchronous function (see below), but a non-asynchronous version can be done with
PyElucidate's helper functions.

Search by annotation target:

.. code-block:: python

    from pyelucidate import pyelucidate
    import requests
    import json

    # generate a search to Elucidate, using Elucidate's search API to search target id and target source
    search_uri = pyelucidate.gen_search_by_target_uri(elucidate_base="https://elucidate.example.org", model="w3c",
                                                      target_uri="http://iiif.example.org/iiif/manfiest/1/canvas/4",
                                                      field=["id", "source"])

    r = requests.get(search_uri)

    annotations = []

    if r.status_code == requests.codes.ok:
        for page in pyelucidate.annotation_pages(r.json()):  # PyElucidate helper for handling activity streams paging.
            annotations.extend(requests.get(page).json()["items"])

    print(json.dumps(annotations, indent=4))


Search by container (assumes the container is an MD5 hash of the target URI):

.. code-block:: python

    from pyelucidate import pyelucidate
    import requests
    import json

    # generate a search to Elucidate, using Elucidate's search API to request a container's contents
    search_uri = pyelucidate.gen_search_by_container_uri(elucidate_base="https://elucidate.glam-dev.org", model="w3c",
                                                         target_uri="http://iiif.example.org/iiif/manfiest/1/canvas/4")


    r = requests.get(search_uri)

    annotations = []

    if r.status_code == requests.codes.ok:
        for page in pyelucidate.annotation_pages(r.json()):  # PyElucidate helper for handling activity streams paging.
            annotations.extend(requests.get(page).json()["items"])

    print(json.dumps(annotations, indent=4))


Parents by body source
----------------------

Query Elucidate for all annotations with a specified body source, and return a list of parents.

Typical usage:

    For tagging annotations, where the target is tagged with a particular topic URI, return all parent manifests for
    canvases that have been tagged with that topic URI.


Bulk update
-----------

Placeholder

Bulk delete
-----------

Placeholder

Asynchronous functions
======================

Elucidate provides a number of additional services which extend the W3C Web Annotation Protocol. PyElucidate provides
asynchronous versions of these functions which can make parallel requests for efficient return of results.
