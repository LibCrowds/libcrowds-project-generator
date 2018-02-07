# -*- coding: utf8 -*-
"""JSON volume exporter module for pybossa-lc."""

import json
import tempfile
from collections import namedtuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from pybossa.core import uploader

from . import VolumeExporter


class JsonVolumeExporter(VolumeExporter):

    def _respond_json(self, ty, volume_id):
        export_data = self._get_data(ty, volume_id)
        return {'test': '123'}

    def _make_zip(self, volume, ty):
        name = self._project_name_latin_encoded(volume)
        json_data_generator = self._respond_json(ty, volume.id)
        if json_data_generator is not None:
            datafile = tempfile.NamedTemporaryFile()
            try:
                datafile.write(json.dumps(json_data_generator))
                datafile.flush()
                zipped_datafile = tempfile.NamedTemporaryFile()
                try:
                    _zip = self._zip_factory(zipped_datafile.name)
                    fn = '%s_%s.json' % (name, ty)
                    _zip.write(datafile.name, secure_filename(fn))
                    _zip.close()
                    container = self._container(volume)
                    dl_fn = self.download_name(volume, ty)
                    _file = FileStorage(filename=dl_fn, stream=zipped_datafile)
                    uploader.upload_file(_file, container=container)
                finally:
                    zipped_datafile.close()
            finally:
                datafile.close()

    def download_name(self, volume, ty):
        return super(JsonVolumeExporter, self).download_name(volume, ty,
                                                             'json')

    def pregenerate_zip_files(self, category):
        print "%d (json)" % category.id
        for volume in category.info.get('volumes', []):
            self._make_zip(volume, volume.name)