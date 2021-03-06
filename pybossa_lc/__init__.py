# -*- coding: utf8 -*-
"""Main package for pybossa-lc."""

import os
import json
from flask import current_app as app
from flask.ext.plugins import Plugin
from pybossa.extensions import importer

from . import default_settings
from .extensions import *
from .importers.iiif_enhanced import BulkTaskIIIFEnhancedImporter


__plugin__ = "PyBossaLC"
__version__ = json.load(open(os.path.join(os.path.dirname(__file__),
                                          'info.json')))['version']


class PyBossaLC(Plugin):
    """A PYBOSSA plugin for managing LibCrowds projects."""

    def setup(self):
        """Setup plugin."""
        self.configure()
        self.setup_blueprints()
        self.setup_enhanced_iiif_importer()
        wa_client.init_app(app)

    def configure(self):
        """Load configuration settings."""
        settings = [key for key in dir(default_settings) if key.isupper() and
                    not key.startswith('#')]
        for s in settings:
            if not app.config.get(s):
                app.config[s] = getattr(default_settings, s)

    def setup_blueprints(self):
        """Setup blueprints."""
        from .api.analysis import BLUEPRINT as analysis
        from .api.projects import BLUEPRINT as projects
        from .api.categories import BLUEPRINT as categories
        from .api.admin import BLUEPRINT as admin
        from .api.proxy import BLUEPRINT as proxy
        app.register_blueprint(analysis, url_prefix='/lc/analysis')
        app.register_blueprint(projects, url_prefix='/lc/projects')
        app.register_blueprint(categories, url_prefix='/lc/categories')
        app.register_blueprint(admin, url_prefix='/lc/admin')
        app.register_blueprint(proxy, url_prefix='/lc/proxy')

    def setup_enhanced_iiif_importer(self):
        """Setup the enhanced IIIF manifest importer."""
        importer._importers['iiif-enhanced'] = BulkTaskIIIFEnhancedImporter
