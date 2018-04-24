# -*- coding: utf8 -*-
"""Annotations API module for pybossa-lc."""

import json
from flask import Blueprint, abort, make_response, request, current_app
from werkzeug.exceptions import default_exceptions
from pybossa.core import project_repo

from ..cache import annotations as annotations_cache
from .. import volume_repo

try:
    from urllib import urlencode
except ImportError:  # py3
    from urllib.parse import urlencode


BLUEPRINT = Blueprint('lc_annotations', __name__)


def jsonld_response(body, status_code=200):
    """Return a valid JSON-LD annotation response.

    See https://www.w3.org/TR/annotation-protocol/#annotation-retrieval
    """
    response = make_response(json.dumps(body), status_code)
    profile = '"http://www.w3.org/ns/anno.jsonld"'
    response.mimetype = 'application/ld+json; profile={0}'.format(profile)
    link = '<http://www.w3.org/ns/ldp#Resource>; rel="type"'
    response.headers['Link'] = link
    response.headers['Allow'] = 'GET,OPTIONS,HEAD'
    response.headers['Vary'] = 'Accept'
    response.add_etag()
    response.status_code = status_code
    return response


def jsonld_abort(status_code):
    """Abort wtih valid JSON-LD response."""
    body = {'code': status_code}

    if status_code in default_exceptions:
        body['message'] = default_exceptions[status_code].description
    else:
        body['message'] = 'Server Error'

    return jsonld_response(body, status_code=status_code)


@BLUEPRINT.route('/wa/<annotation_id>')
def get_wa(annotation_id):
    """Return an Annotation."""
    spa_server_name = current_app.config.get('SPA_SERVER_NAME')
    full_id = '{0}/lc/annotations/wa/{1}'.format(spa_server_name,
                                                 annotation_id)
    anno = annotations_cache.get(full_id)
    if not anno:
        return jsonld_abort(404)

    return jsonld_response(anno)


@BLUEPRINT.route('/wa/collection/volume/<volume_id>')
def get_volume_collection(volume_id):
    """Return an Annotation Collection for a volume."""
    volume = volume_repo.get(volume_id)
    if not volume:
        return jsonld_abort(404)

    motivation = request.args.get('motivation')
    annotations = annotations_cache.get_by_volume(volume_id, motivation)

    spa_server_name = current_app.config.get('SPA_SERVER_NAME')
    url_base = '{0}/lc/annotations/wa/collection/volume/{1}'

    per_page = current_app.config.get('ANNOTATIONS_PER_PAGE')
    last = 1 if not annotations else ((len(annotations) - 1) // per_page) + 1

    id_uri = url_base.format(spa_server_name, volume_id)
    first_uri = "{0}/1".format(id_uri)
    last_uri = "{0}/{1}".format(id_uri, last)

    if request.args:
        query_str = urlencode(request.args)
        id_uri += "?{}".format(query_str)
        first_uri += "?{}".format(query_str)
        last_uri += "?{}".format(query_str)

    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": id_uri,
        "type": "AnnotationCollection",
        "label": "{0} Annotations".format(volume.name),
        "total": len(annotations),
        "first": first_uri,
        "last": last_uri
    }

    return jsonld_response(data)


@BLUEPRINT.route('/wa/collection/volume/<volume_id>/<int:page>')
def get_volume_page(volume_id, page):
    """Return an Annotation Page for a volume."""
    volume = volume_repo.get(volume_id)
    if not volume:
        return jsonld_abort(404)

    motivation = request.args.get('motivation')
    annotations = annotations_cache.get_by_volume(volume_id, motivation)

    spa_server_name = current_app.config.get('SPA_SERVER_NAME')
    url_base = '{0}/lc/annotations/wa/collection/volume/{1}'

    per_page = current_app.config.get('ANNOTATIONS_PER_PAGE')
    last = 1 if not annotations else ((len(annotations) - 1) // per_page) + 1
    if page > last:
        return jsonld_abort(404)

    anno_collection_uri = url_base.format(spa_server_name, volume_id)
    id_uri = "{0}/{1}".format(anno_collection_uri, page)
    next_uri = "{0}/{1}".format(anno_collection_uri, page + 1)

    if request.args:
        query_str = urlencode(request.args)
        id_uri += "?{}".format(query_str)
        anno_collection_uri += "?{}".format(query_str)
        next_uri += "?{}".format(query_str)

    items = annotations[per_page * (page - 1):per_page * page]
    if request.args.get('iris'):
        items = [item['id'] for item in items]

    data = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": id_uri,
        "type": "AnnotationPage",
        "partOf": {
            "id": anno_collection_uri,
            "label": "{0} Annotations".format(volume.name),
            "total": len(annotations)
        },
        "startIndex": 0,
        "items": items
    }

    if last > page:
        data['next'] = next_uri

    return jsonld_response(data)
