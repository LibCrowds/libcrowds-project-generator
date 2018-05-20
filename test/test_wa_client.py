# -*- coding: utf8 -*-

import json
from nose.tools import *
from mock import patch, call
from default import Test, flask_app

from pybossa_lc import wa_client
from .fixtures.response import MockResponse


class TestWAClient(Test):

    def setUp(self):
        super(TestWAClient, self).setUp()

    @patch('pybossa_lc.web_annotation_client.requests')
    def test_create_annotation(self, mock_requests):
        """Test create Annotation."""
        iri = 'example.com'
        anno = {
          'body': 'foo',
          'target': 'bar'
        }
        expected = {
          'id': 'baz',
          'body': 'foo',
          'target': 'bar'
        }
        fake_resp = MockResponse(json.dumps(expected))
        mock_requests.post.return_value = fake_resp

        result = wa_client.create_annotation(iri, anno)
        mock_requests.post.assert_called_once_with(iri, data=json.dumps(anno))
        assert_dict_equal(result, expected)

    @patch('pybossa_lc.web_annotation_client.requests')
    def test_get_collection(self, mock_requests):
        """Test get AnnotationCollection."""
        iri = 'example.com'
        ns = 'http://www.w3.org/ns/oa#PreferContainedDescriptions'
        headers = {
            'Prefer': 'return=representation; include="{}"'.format(ns)
        }
        expected = {
          'id': 'foo',
          'label': 'bar'
        }
        fake_resp = MockResponse(json.dumps(expected))
        mock_requests.get.return_value = fake_resp

        result = wa_client.get_collection(iri)
        mock_requests.get.assert_called_once_with(iri, headers=headers)
        assert_dict_equal(result, expected)

    def test_get_prefer_headers(self):
        """Test get Prefer headers."""
        base = 'return=representation; include="{0}"'
        default = wa_client._get_prefer_headers()
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedDescriptions'
        ]
        assert_equal(default, base.format(' '.join(ns)))
        minimal = wa_client._get_prefer_headers(minimal=True)
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedDescriptions',
          'http://www.w3.org/ns/ldp#PreferMinimalContainer'
        ]
        assert_equal(minimal, base.format(' '.join(ns)))
        iris = wa_client._get_prefer_headers(iris=True)
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedIRIs'
        ]
        assert_equal(iris, base.format(' '.join(ns)))
        minimal_iris = wa_client._get_prefer_headers(minimal=True, iris=True)
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedIRIs',
          'http://www.w3.org/ns/ldp#PreferMinimalContainer'
        ]
        assert_equal(minimal_iris, base.format(' '.join(ns)))

    @patch('pybossa_lc.web_annotation_client.requests')
    def test_search_annotations(self, mock_requests):
        """Test search Annotations."""
        collection_id = 'foo'
        iri = 'example.com/{}'.format(collection_id)
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedDescriptions',
          'http://www.w3.org/ns/ldp#PreferMinimalContainer'
        ]
        base_prefer = 'return=representation; include="{}"'
        headers = {
            'Prefer': base_prefer.format(' '.join(ns))
        }
        contains = {'bar': 'baz'}
        params = {
            'collection.id': collection_id,
            'contains': contains
        }
        fake_collection = {
          'total': 0
        }
        fake_resp = MockResponse(json.dumps(fake_collection))
        mock_requests.get.return_value = fake_resp
        base_url = flask_app.config.get('WEB_ANNOTATION_BASE_URL')
        endpoint = base_url + '/search/annotations'

        result = wa_client.search_annotations(iri, contains)
        mock_requests.get.assert_called_once_with(endpoint, headers=headers,
                                                  params=params)
        assert_equal(result, [])

    @patch('pybossa_lc.web_annotation_client.requests')
    def test_search_annotations_with_pages(self, mock_requests):
        """Test search Annotations with multiple pages."""
        collection_id = 'foo'
        iri = 'example.com/{}'.format(collection_id)
        ns = [
          'http://www.w3.org/ns/oa#PreferContainedDescriptions',
          'http://www.w3.org/ns/ldp#PreferMinimalContainer'
        ]
        base_prefer = 'return=representation; include="{}"'
        headers = {
            'Prefer': base_prefer.format(' '.join(ns))
        }
        contains = {'bar': 'baz'}
        params = {
            'collection.id': collection_id,
            'contains': contains
        }
        fake_collection = {
          'total': 10,
          'first': 'http://annotations.example.com/page1'
        }
        fake_page1 = {
          'total': 10,
          'items': [1, 2, 3, 4, 5],
          'next': 'http://annotations.example.com/page2'
        }
        fake_page2 = {
          'total': 10,
          'items': [6, 7, 8, 9, 10]
        }
        mock_requests.get.side_effect = [
          MockResponse(json.dumps(fake_collection)),
          MockResponse(json.dumps(fake_page1)),
          MockResponse(json.dumps(fake_page2))
        ]
        base_url = flask_app.config.get('WEB_ANNOTATION_BASE_URL')
        endpoint = base_url + '/search/annotations'

        result = wa_client.search_annotations(iri, contains)
        assert_equal(mock_requests.get.call_args_list, [
          call(endpoint, headers=headers, params=params),
          call(fake_collection['first']),
          call(fake_page1['next'])
        ])
        assert_equal(result, fake_page1['items'] + fake_page2['items'])