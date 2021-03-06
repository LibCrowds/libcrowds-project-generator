# -*- coding: utf8 -*-
"""API admin module for pybossa-lc."""

import json
from flask import Blueprint, abort, flash, request, current_app, Response
from flask.ext.login import login_required
from flask_wtf.csrf import generate_csrf
from pybossa.util import handle_content_type, admin_required
from pybossa.core import project_repo
from pybossa.model import make_uuid

from ..jobs import analyse_all, analyse_empty


BLUEPRINT = Blueprint('lc_admin', __name__)


@login_required
@admin_required
@BLUEPRINT.route('/results/analyse/all/<int:category_id>',
                 methods=['GET', 'POST'])
def analyse_all_results(category_id):
    """Analyse all results for a category."""
    category = project_repo.get_category(category_id)
    if not category:
        abort(404)

    if request.method == 'POST':
        presenter = category.info.get('presenter')
        projects = project_repo.filter_by(category_id=category.id)
        for project in projects:
            analyse_all(project.id, presenter)
        flash('Analysis of all results queued', 'success')
        csrf = None
    else:
        csrf = generate_csrf()

    response = dict(csrf=csrf)
    return handle_content_type(response)


@login_required
@admin_required
@BLUEPRINT.route('/results/analyse/empty/<int:category_id>',
                 methods=['GET', 'POST'])
def analyse_empty_results(category_id):
    """Analyse empty results for a category."""
    category = project_repo.get_category(category_id)
    if not category:
        abort(404)

    if request.method == 'POST':
        presenter = category.info.get('presenter')
        projects = project_repo.filter_by(category_id=category.id)
        for project in projects:
            analyse_empty(project.id, presenter)
        flash('Analysis of empty results queued', 'success')
        csrf = None
    else:
        csrf = generate_csrf()

    response = dict(csrf=csrf)
    return handle_content_type(response)


@login_required
@admin_required
@BLUEPRINT.route('/templates', methods=['GET'])
def get_template_framework():
    """Return the fields required for different parts of a template.

    A simple way to ensure we have the fields needed for the rest of this
    plugin. It will be up to the frontend to handle CRUD.
    """
    base = {
        'id': make_uuid(),
        'name': '',
        'description': '',
        'parent_template_id': None,
        'min_answers': 3,
        'max_answers': 3,
        'tutorial': ''
    }

    task = {
        'z3950': {
            'database': '',   # a key in z3950_databases
            'institutions': []
        },
        'iiif-annotation': {
            'mode': '',  # select or transcribe
            'tag': '',
            'objective': '',
            'guidance': '',
            'reject': [],
            'fields_schema': []  # Populated with vue-multiselect fields
        }
    }

    rules = {
        'whitespace': '',  # normalise, underscore or full_stop (if any)
        'case': '',  # title, lower or upper (if any)
        'trim_punctuation': False,
        'date_format': False,
        'dayfirst': False,
        'year_first': False,
        'remove_fragment_selector': False
    }

    z3950_databases = current_app.config.get('Z3950_DATABASES', {}).keys()
    response = dict(base=base, rules=rules, task=task,
                    z3950_databases=z3950_databases)
    return Response(json.dumps(response), mimetype='application/json')
