# -*- coding: utf8 -*-
"""Test category API."""

import json
import uuid
from mock import patch, MagicMock
from nose.tools import *
from helper import web
from default import with_context, db, Fixtures
from factories import CategoryFactory, UserFactory
from pybossa.repositories import UserRepository, ProjectRepository
from pybossa.jobs import import_tasks

from ..fixtures import TemplateFixtures


class TestCategoryApi(web.Helper):

    def setUp(self):
        super(TestCategoryApi, self).setUp()
        self.category = CategoryFactory()
        self.tmpl_fixtures = TemplateFixtures(self.category)
        self.user_repo = UserRepository(db)
        self.project_repo = ProjectRepository(db)

    @with_context
    def test_user_templates_listed(self):
        """Test all of a user's templates are listed."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        endpoint = '/lc/users/{}/templates'.format(Fixtures.name)
        res = self.app_get_json(endpoint)
        data = json.loads(res.data)
        assert_equal(data['templates'], [tmpl])
        assert_equal(data['form']['errors'], {})

    @with_context
    def test_get_template_by_id(self):
        """Test get template by ID for owner."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        endpoint = '/lc/users/{}/templates/{}'.format(user.name, tmpl['id'])
        res = self.app_get_json(endpoint)
        data = json.loads(res.data)
        assert_equal(data['template'], tmpl)

    @with_context
    def test_add_template(self):
        """Test that a template is added."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        tmpl = self.tmpl_fixtures.create_template()

        endpoint = '/lc/users/{}/templates'.format(Fixtures.name)
        res = self.app_post_json(endpoint, data=tmpl)
        data = json.loads(res.data)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        templates = updated_user.info.get('templates')
        assert_equal(data['flash'], 'New template submitted for approval')
        assert_equal(len(templates), 1)
        tmpl_id = templates[0].pop('id')
        print templates[0]
        print tmpl
        assert_dict_equal(templates[0], tmpl)

        # Check redirect to update page
        next_url = '/lc/users/{0}/templates/{1}'.format(Fixtures.name, tmpl_id)
        assert_equal(data['next'], next_url)

    @with_context
    def test_update_project_template(self):
        """Test that project template data is updated."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        tmpl['name'] = 'Some updated name'
        tmpl['pending'] = False
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        url_base = '/lc/users/{}/templates/{}'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=tmpl)

        data = json.loads(res.data)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        templates = updated_user.info.get('templates')
        tmpl['pending'] = True
        assert_equal(data['flash'], 'Template updates submitted for approval')
        assert_equal(len(templates), 1)
        assert_dict_equal(templates[0], tmpl)

    @with_context
    def test_add_iiif_transcribe_task(self):
        """Test a IIIF transcribe task is added to a template."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        user.info['templates'] = [tmpl]
        tmpl['pending'] = False
        self.user_repo.update(user)

        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/lc/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint,
                                 data=self.tmpl_fixtures.iiif_transcribe_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.iiif_transcribe_tmpl
        tmpl['pending'] = True
        assert_equal(json.loads(res.data)['flash'],
                     'Template updates submitted for approval')

        assert_equal(len(user_templates), 1)
        assert_dict_equal(user_templates[0], tmpl)

    @with_context
    def test_add_iiif_select_task(self):
        """Test a IIIF select task is added."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        tmpl['pending'] = False
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/lc/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint,
                                 data=self.tmpl_fixtures.iiif_select_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.iiif_select_tmpl
        tmpl['pending'] = True
        assert_equal(json.loads(res.data)['flash'],
                     'Template updates submitted for approval')
        assert_equal(len(user_templates), 1)
        assert_dict_equal(user_templates[0], tmpl)

    @with_context
    def test_add_z3950_task(self):
        """Test a Z39.50 task is added."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        tmpl['pending'] = False
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.category.info = dict(presenter='z3950')
        self.project_repo.update_category(self.category)

        url_base = '/lc/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.z3950_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.z3950_tmpl
        tmpl['pending'] = True
        assert_equal(json.loads(res.data)['flash'],
                     'Template updates submitted for approval')
        assert_equal(len(user_templates), 1)
        assert_dict_equal(user_templates[0], tmpl)

    @with_context
    def test_update_task_template(self):
        """Test a task template is updated."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        task_tmpl = self.tmpl_fixtures.iiif_select_tmpl
        tmpl = self.tmpl_fixtures.create_template(task_tmpl=task_tmpl)
        tmpl['pending'] = False
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        tmpl['task']['mode'] = 'transcribe'
        tmpl['task']['fields_schema'] = []
        url_base = '/lc/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=tmpl['task'])

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['pending'] = True
        assert_equal(json.loads(res.data)['flash'],
                     'Template updates submitted for approval')
        assert_equal(len(user_templates), 1)
        assert_dict_equal(user_templates[0], tmpl)

    @with_context
    def test_analysis_rules_are_added_for_iiif_transcribe_templates(self):
        """Test analysis rules are added for IIIF transcribe templates."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        task_tmpl = self.tmpl_fixtures.iiif_transcribe_tmpl
        tmpl = self.tmpl_fixtures.create_template(task_tmpl)
        tmpl['pending'] = False
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/lc/users/{}/templates/{}/rules'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.rules_tmpl)

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['pending'] = True
        msg = 'Template updates submitted for approval'
        assert_equal(json.loads(res.data)['flash'], msg)
        assert_equal(len(user_templates), 1)
        assert_equal(user_templates[0]['rules'], self.tmpl_fixtures.rules_tmpl)
