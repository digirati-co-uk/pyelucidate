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




GET an annotation
-----------------

Will fetch the annotation and return annotation plus the ETag for the annotation.

.. code-block:: python

    from pyelucidate import pyelucidate
    import json

    annotation, etag = pyelucidate.read_anno("https://elucidate.glam-dev.org/annotation/w3c"
                              "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")


DELETE an annotation
--------------------

The W3C Web Annotation Protocol requires an ``If-Match`` header with the ETag for the
annotation. This function requires the ETag to be provided.

If ``dry_run`` is ``True`` (the default), the function will return a 204 without deleting the annotation.

The example below shows fetching an annotation, checking the purpose for the body, and deleting the annotation.


.. code-block:: python

    from pyelucidate import pyelucidate

    annotation, etag = pyelucidate.read_anno("https://elucidate.glam-dev.org/annotation/w3c"
                              "/36b74ab23429078e9a8631ed4a471095/0ef3db79-c6a0-4755-a0a1-8ba660f81e93")


    if annotation["body"]["purpose"] == "tagging":
        status = pyelucidate.delete_anno(anno_uri = annotation["id"], etag=etag, dry_run=False)
        assert status == 204


BBBB
