# -*- coding: utf8 -*-
"""Annotation fixtures."""

import uuid
from default import flask_app


class AnnotationFixtures(object):

    def create(self, motivation='describing', source=None, tag=None,
               value=None):
        anno = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": str(uuid.uuid4()),
            "type": "Annotation",
            "motivation": motivation,
        }

        if motivation == 'describing':
            anno.update({
                "body": [
                    {
                        "type": "TextualBody",
                        "purpose": "describing",
                        "value": value,
                        "format": "text/plain"
                    },
                    {
                        "type": "TextualBody",
                        "purpose": "tagging",
                        "value": tag
                    }
                ],
                "target": source
            })

        elif motivation == 'tagging':
            anno.update({
                "body": [
                    {
                        "type": "TextualBody",
                        "purpose": "tagging",
                        "value": tag
                    },
                ],
                "target": {
                    "source": source,
                    "selector": {
                        "conformsTo": "http://www.w3.org/TR/media-frags/",
                        "type": "FragmentSelector",
                        "value": value
                    }
                }
            })

        elif motivation == 'commenting':
            anno.update({
                "body": {
                    "type": "TextualBody",
                    "purpose": "commenting",
                    "value": value,
                    "format": "text/plain"
                },
                "target": source
            })

        else:
            raise ValueError('Invalid motivation')

        return anno
