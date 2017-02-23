#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from nose.plugins.skip import SkipTest
from nose.tools import assert_equal

from django.core.cache import cache
from django.contrib.auth.models import User

from desktop.auth.backend import rewrite_user
from desktop.lib.django_test_util import make_logged_in_client
from desktop.lib.test_utils import add_to_group, grant_access
from hadoop.pseudo_hdfs4 import is_live_cluster

from metadata.conf import has_navigator, NAVIGATOR
from metadata.navigator_client import NavigatorApi
from libsentry.privilege_checker import SENTRY_PRIVILEGE_CACHE_KEY,\
  PrivilegeChecker
from libsentry.test_privilege_checker import MockSentryApiV2


LOG = logging.getLogger(__name__)


class MockedRoot():
  def get(self, relpath=None, params=None, headers=None, clear_cookies=False):
    return params


class NavigatorClientTest:

  @classmethod
  def setup_class(cls):
    cls.client = make_logged_in_client(username='test', is_superuser=False)
    cls.user = User.objects.get(username='test')
    cls.user = rewrite_user(cls.user)
    add_to_group('test')
    grant_access("test", "test", "metadata")

    if not has_navigator(cls.user):
      raise SkipTest

    cls.api = NavigatorApi(cls.user)
    cls.api._root = MockedRoot()


class MockSentryApiHive(object):

  def __init__(self, privileges=None):
    self.privileges = privileges or []


  def list_sentry_roles_by_group(self, *args, **kwargs):
    return [{'name': 'test', 'group': 'test'}]


  def list_sentry_privileges_by_role(self, *args, **kwargs):
    return self.privileges



class TestNavigatorClientSecure(NavigatorClientTest):

  def setUp(self):
    self.reset = NAVIGATOR.APPLY_SENTRY_PERMISSIONS.set_for_testing(True)

  def tearDown(self):
    self.reset()


  def test_secure_results(self):

    cache_key = SENTRY_PRIVILEGE_CACHE_KEY % {'username': self.user.username}

    try:
      api_v1 = MockSentryApiHive(privileges=[
        {'column': '', 'grantOption': False, 'timestamp': 1478810513849, 'database': 'etl', 'action': 'SELECT', 'scope': 'DATABASE', 'table': '', 'URI': '', 'server': 'server1'},
        {'column': '', 'grantOption': False, 'timestamp': 1478810422058, 'database': 'etl', 'action': 'SELECT', 'scope': 'TABLE', 'table': 'finance', 'URI': '', 'server': 'server1'},
        {'column': 'col3', 'grantOption': False, 'timestamp': 1478810590335, 'database': 'etl', 'action': 'SELECT', 'scope': 'TABLE', 'table': 'finance', 'URI': '', 'server': 'server1'},
      ])
      api_v2 = MockSentryApiV2()
      checker = PrivilegeChecker(user=self.user, api_v1=api_v1, api_v2=api_v2)

      records = [
        {u'type': u'DATABASE', u'originalName': u'etl', u'description': None, u'params': None, u'internalType': u'hv_database', u'sourceType': u'HIVE', u'tags': None, u'originalDescription': None, u'metaClassName': u'hv_database', u'properties': None, u'identity': u'51002517', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##3', u'sourceId': u'56850544', u'packageName': u'nav', u'parentPath': None},
        {u'type': u'TABLE', u'parentPath': u'/etl', u'originalName': u'finance', u'clusteredByColNames': None, u'customProperties': None, u'owner': u'elt', u'serdeName': None, u'sourceType': u'HIVE', u'serdeLibName': u'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe', u'internalType': u'hv_table', u'description': None, u'tags': None, u'originalDescription': None, u'compressed': False, u'metaClassName': u'hv_table', u'properties': None, u'identity': u'51340470', u'outputFormat': u'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1185', u'created': u'2015-08-14T00:04:01.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'lastAccessed': u'1970-01-01T00:00:00.000Z'},
        {u'type': u'FIELD', u'parentPath': u'/etl/finance', u'originalName': u'col1', u'customProperties': None, u'deleteTime': None, u'description': None, u'dataType': u'string', u'internalType': u'hv_column', u'sourceType': u'HIVE', u'tags': None, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_column', u'properties': None, u'identity': u'51001004', u'firstClassParentId': u'59444965', u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1582', u'sourceId': u'56850544', u'packageName': u'nav'},
        {u'type': u'VIEW', u'parentPath': u'/etl', u'originalName': u'finance_view', u'customProperties': None, u'deleteTime': None, u'description': None, u'lastModifiedBy': None, u'internalType': u'hv_view', u'sourceType': u'HIVE', u'tags': None, u'deleted': False, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_view', u'properties': None, u'identity': u'51012354', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##394', u'created': u'2015-09-02T08:01:14.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'queryText': u"SELECT * FROM etl.finance LIMIT 10", u'lastAccessed': u'1970-01-01T00:00:00.000Z'}
      ]

      results = list(self.api._secure_results(records, checker=checker))
      assert_equal(len(records), len(results), results)

      # No privilege
      api_v1 = MockSentryApiHive()
      checker = PrivilegeChecker(user=self.user, api_v1=api_v1, api_v2=api_v2)

      records = [
        {u'type': u'DATABASE', u'originalName': u'etl', u'description': None, u'params': None, u'internalType': u'hv_database', u'sourceType': u'HIVE', u'tags': None, u'originalDescription': None, u'metaClassName': u'hv_database', u'properties': None, u'identity': u'51002517', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##3', u'sourceId': u'56850544', u'packageName': u'nav', u'parentPath': None},
        {u'type': u'TABLE', u'parentPath': u'/etl', u'originalName': u'finance', u'clusteredByColNames': None, u'customProperties': None, u'owner': u'elt', u'serdeName': None, u'sourceType': u'HIVE', u'serdeLibName': u'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe', u'internalType': u'hv_table', u'description': None, u'tags': None, u'originalDescription': None, u'compressed': False, u'metaClassName': u'hv_table', u'properties': None, u'identity': u'51340470', u'outputFormat': u'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1185', u'created': u'2015-08-14T00:04:01.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'lastAccessed': u'1970-01-01T00:00:00.000Z'},
        {u'type': u'FIELD', u'parentPath': u'/etl/finance', u'originalName': u'col1', u'customProperties': None, u'deleteTime': None, u'description': None, u'dataType': u'string', u'internalType': u'hv_column', u'sourceType': u'HIVE', u'tags': None, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_column', u'properties': None, u'identity': u'51001004', u'firstClassParentId': u'59444965', u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1582', u'sourceId': u'56850544', u'packageName': u'nav'},
        {u'type': u'VIEW', u'parentPath': u'/etl', u'originalName': u'finance_view', u'customProperties': None, u'deleteTime': None, u'description': None, u'lastModifiedBy': None, u'internalType': u'hv_view', u'sourceType': u'HIVE', u'tags': None, u'deleted': False, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_view', u'properties': None, u'identity': u'51012354', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##394', u'created': u'2015-09-02T08:01:14.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'queryText': u"SELECT * FROM etl.finance LIMIT 10", u'lastAccessed': u'1970-01-01T00:00:00.000Z'}
      ]

      results = list(self.api._secure_results(records, checker=checker))
      assert_equal(0, len(results), results)

      # All privileges
      api_v1 = MockSentryApiHive(privileges=[
        # Table SELECT
        {'column': '', 'grantOption': False, 'timestamp': 1478810422058, 'database': 'etl', 'action': 'SELECT', 'scope': 'TABLE', 'table': 'finance', 'URI': '', 'server': 'server1'},
      ])
      checker = PrivilegeChecker(user=self.user, api_v1=api_v1, api_v2=api_v2)

      records = [
        {u'type': u'DATABASE', u'originalName': u'etl', u'description': None, u'params': None, u'internalType': u'hv_database', u'sourceType': u'HIVE', u'tags': None, u'originalDescription': None, u'metaClassName': u'hv_database', u'properties': None, u'identity': u'51002517', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##3', u'sourceId': u'56850544', u'packageName': u'nav', u'parentPath': None},
        {u'type': u'TABLE', u'parentPath': u'/etl', u'originalName': u'finance', u'clusteredByColNames': None, u'customProperties': None, u'owner': u'elt', u'serdeName': None, u'sourceType': u'HIVE', u'serdeLibName': u'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe', u'internalType': u'hv_table', u'description': None, u'tags': None, u'originalDescription': None, u'compressed': False, u'metaClassName': u'hv_table', u'properties': None, u'identity': u'51340470', u'outputFormat': u'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1185', u'created': u'2015-08-14T00:04:01.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'lastAccessed': u'1970-01-01T00:00:00.000Z'},
        {u'type': u'FIELD', u'parentPath': u'/etl/finance', u'originalName': u'col1', u'customProperties': None, u'deleteTime': None, u'description': None, u'dataType': u'string', u'internalType': u'hv_column', u'sourceType': u'HIVE', u'tags': None, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_column', u'properties': None, u'identity': u'51001004', u'firstClassParentId': u'59444965', u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##1582', u'sourceId': u'56850544', u'packageName': u'nav'},
        {u'type': u'VIEW', u'parentPath': u'/etl', u'originalName': u'finance_view', u'customProperties': None, u'deleteTime': None, u'description': None, u'lastModifiedBy': None, u'internalType': u'hv_view', u'sourceType': u'HIVE', u'tags': None, u'deleted': False, u'technicalProperties': None, u'userEntity': False, u'originalDescription': None, u'metaClassName': u'hv_view', u'properties': None, u'identity': u'51012354', u'firstClassParentId': None, u'name': None, u'extractorRunId': u'845beb21b95783c4f55276a4ae38a332##394', u'created': u'2015-09-02T08:01:14.000Z', u'sourceId': u'56850544', u'lastModified': None, u'packageName': u'nav', u'queryText': u"SELECT * FROM etl.finance LIMIT 10", u'lastAccessed': u'1970-01-01T00:00:00.000Z'}
      ]

      results = list(self.api._secure_results(records, checker=checker))
      assert_equal(2, len(results), results) # Table + its Column
    finally:
      cache.delete(cache_key)


class TestNavigatorClientTest(NavigatorClientTest):

  def setUp(self):
    self.reset = NAVIGATOR.APPLY_SENTRY_PERMISSIONS.set_for_testing(False)

  def tearDown(self):
    self.reset()

  def test_search_entities(self):
    assert_equal(
        '((originalName:*cases*)OR(originalDescription:*cases*)OR(name:*cases*)OR(description:*cases*)OR(tags:*cases*)) AND (*) AND ((type:TABLE)OR(type:VIEW))',
        self.api.search_entities(query_s='cases', sources=['hive'])[0][1]
    )

    assert_equal(
        '* AND ((type:FIELD*)) AND ((type:TABLE)OR(type:VIEW)OR(type:DATABASE)OR(type:PARTITION)OR(type:FIELD))',
        self.api.search_entities(query_s='type:FIELD', sources=['hive'])[0][1]
    )

    # type:
    # type:VIEW
    # type:VIEW ca
    # type:VIEW ca owner:hue
    # type:(VIEW OR TABLE)
    # type:(VIEW OR TABLE) ca
    # ca es
    # "ca es"
    # ca OR es
    # tags:a

    # type:table tax
    # owner:romain ca

    # *