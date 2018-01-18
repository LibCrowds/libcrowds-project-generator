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
        endpoint = '/libcrowds/users/{}/templates'.format(Fixtures.name)
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
        endpoint = '/libcrowds/users/{}/templates/{}'.format(user.name,
                                                             tmpl['id'])
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

        endpoint = '/libcrowds/users/{}/templates'.format(Fixtures.name)
        res = self.app_post_json(endpoint, data=tmpl['project'],
                                 follow_redirects=True)
        data = json.loads(res.data)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        templates = updated_user.info.get('templates')
        assert_equal(data['flash'], 'Project template created')
        assert_equal(len(templates), 1)
        tmpl_id = templates[0].pop('id')
        expected = dict(project=self.tmpl_fixtures.project_tmpl, task=None,
                        rules=None)
        assert_dict_equal(templates[0], expected)

        # Check redirect to update page
        next_url = '/libcrowds/users/{0}/templates/{1}'.format(Fixtures.name,
                                                               tmpl_id)
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
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        url_base = '/libcrowds/users/{}/templates/{}'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=tmpl['project'])

        data = json.loads(res.data)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        templates = updated_user.info.get('templates')
        assert_equal(data['flash'], 'Project template updated')
        assert_equal(len(templates), 1)
        assert_dict_equal(templates[0]['project'], tmpl['project'])

    @with_context
    def test_add_iiif_transcribe_task(self):
        """Test a IIIF transcribe task is added to a template."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        tmpl = self.tmpl_fixtures.create_template()
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint,
                                 data=self.tmpl_fixtures.iiif_transcribe_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.iiif_transcribe_tmpl
        assert_equal(json.loads(res.data)['flash'], 'Task template updated')

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
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint,
                                 data=self.tmpl_fixtures.iiif_select_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.iiif_select_tmpl
        assert_equal(json.loads(res.data)['flash'], 'Task template updated')
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
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)

        self.category.info = dict(presenter='z3950')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])

        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.z3950_tmpl)
        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        tmpl['task'] = self.tmpl_fixtures.z3950_tmpl
        assert_equal(json.loads(res.data)['flash'], 'Task template updated')
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
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        tmpl['task']['mode'] = 'transcribe'
        tmpl['task']['fields_schema'] = []
        url_base = '/libcrowds/users/{}/templates/{}/task'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=tmpl['task'])

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        assert_equal(json.loads(res.data)['flash'], 'Task template updated')
        assert_equal(len(user_templates), 1)
        assert_dict_equal(user_templates[0], tmpl)

    @with_context
    def test_analysis_rules_not_added_for_z3950_templates(self):
        """Test analysis rules are not added for Z39.50 templates."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        task_tmpl = self.tmpl_fixtures.z3950_tmpl
        tmpl = self.tmpl_fixtures.create_template(task_tmpl)
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='z3950')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/rules'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.rules_tmpl)

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        msg = 'No normalisation rules available for this presenter type'
        assert_equal(json.loads(res.data)['flash'], msg)
        assert_equal(len(user_templates), 1)
        assert_equal(user_templates[0]['rules'], None)

    @with_context
    def test_analysis_rules_not_added_for_iiif_select_templates(self):
        """Test analysis rules are not added for IIIF select templates."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        task_tmpl = self.tmpl_fixtures.iiif_select_tmpl
        tmpl = self.tmpl_fixtures.create_template(task_tmpl)
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/rules'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.rules_tmpl)

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        msg = 'Analysis rules only available for IIIF transcription projects'
        assert_equal(json.loads(res.data)['flash'], msg)
        assert_equal(len(user_templates), 1)
        assert_equal(user_templates[0]['rules'], None)

    @with_context
    def test_analysis_rules_are_added_for_iiif_transcribe_templates(self):
        """Test analysis rules are added for IIIF transcribe templates."""
        self.register(email=Fixtures.email_addr, name=Fixtures.name,
                      password=Fixtures.password)
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        user = self.user_repo.get_by_name(Fixtures.name)
        task_tmpl = self.tmpl_fixtures.iiif_transcribe_tmpl
        tmpl = self.tmpl_fixtures.create_template(task_tmpl)
        user.info['templates'] = [tmpl]
        self.user_repo.update(user)
        self.category.info = dict(presenter='iiif-annotation')
        self.project_repo.update_category(self.category)

        url_base = '/libcrowds/users/{}/templates/{}/rules'
        endpoint = url_base.format(Fixtures.name, tmpl['id'])
        res = self.app_post_json(endpoint, data=self.tmpl_fixtures.rules_tmpl)

        updated_user = self.user_repo.get_by_name(Fixtures.name)
        user_templates = updated_user.info.get('templates')
        msg = 'Results analysis rules updated'
        assert_equal(json.loads(res.data)['flash'], msg)
        assert_equal(len(user_templates), 1)
        assert_equal(user_templates[0]['rules'], self.tmpl_fixtures.rules_tmpl)