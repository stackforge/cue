# -*- coding: utf-8 -*-
# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import cinderclient.client as CinderClient
from keystoneclient.auth.identity import v2 as keystone_v2_auth
from keystoneclient.auth.identity import v3 as keystone_v3_auth
from keystoneclient import session as keystone_session
import neutronclient.neutron.client as NeutronClient
import novaclient.client as NovaClient
from oslo_config import cfg
from oslo_log import log as logging


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


OS_OPTS = [
    cfg.StrOpt('os_region_name',
               help='Region name',
               default=None),
    cfg.StrOpt('os_username',
               help='Openstack Username',
               default=None),
    cfg.StrOpt('os_password',
               help='Openstack Password',
               default=None),
    cfg.StrOpt('os_auth_version',
               help='Openstack authentication version',
               default=None),
    cfg.StrOpt('os_auth_url',
               help='Openstack Authentication (Identity) URL',
               default=None),
    cfg.StrOpt('os_key_name',
               help='SSH key to be provisioned to cue VMs',
               default=None),
    cfg.StrOpt('os_availability_zone',
               help='Default availability zone to provision cue VMs',
               default=None),
    cfg.BoolOpt('os_insecure',
                help='Openstack insecure',
                default=False),
    cfg.StrOpt('os_cacert',
               help='Openstack cacert',
               default=None),
    cfg.StrOpt('os_tenant_name',
               help='Openstack tenant name',
               default=None),
    cfg.StrOpt('os_project_name',
               help='Openstack project name',
               default=None),
    cfg.StrOpt('os_project_domain_name',
               help='Openstack project domain name',
               default=None),
    cfg.StrOpt('os_user_domain_name',
               help='Openstack user domain name',
               default=None),
]

opt_group = cfg.OptGroup(
    name='openstack',
    title='Options for Openstack.'
)

CONF.register_group(opt_group)
CONF.register_opts(OS_OPTS, group=opt_group)


def nova_client():
    keystoneSession = get_keystone_session()
    return NovaClient.Client(2,
                             username=CONF.openstack.os_username,
                             api_key=CONF.openstack.os_password,
                             project_id=CONF.openstack.os_project_name,
                             tenant_id=CONF.openstack.os_tenant_name,
                             auth_url=CONF.openstack.os_auth_url,
                             region_name=CONF.openstack.os_region_name,
                             insecure=CONF.openstack.os_insecure,
                             cacert=CONF.openstack.os_cacert,
                             session=keystoneSession,
                             )


def cinder_client():
    keystoneSession = get_keystone_session()
    return CinderClient.Client('2',
                               username=CONF.openstack.os_username,
                               password=CONF.openstack.os_password,
                               projectid=CONF.openstack.os_project_name,
                               tenant_id=CONF.openstack.os_tenant_name,
                               auth_url=CONF.openstack.os_auth_url,
                               region_name=CONF.openstack.os_region_name,
                               insecure=CONF.openstack.os_insecure,
                               cacert=CONF.openstack.os_cacert,
                               session=keystoneSession,
                               )


def neutron_client():
    keystoneSession = get_keystone_session()
    return NeutronClient.Client('2.0',
                                username=CONF.openstack.os_username,
                                password=CONF.openstack.os_password,
                                auth_url=CONF.openstack.os_auth_url,
                                region_name=CONF.openstack.os_region_name,
                                insecure=CONF.openstack.os_insecure,
                                ca_cert=CONF.openstack.os_cacert,
                                tenant_name=CONF.openstack.os_tenant_name,
                                session=keystoneSession,
                                )


def get_auth_v2():
    return keystone_v2_auth.Password(auth_url=CONF.openstack.os_auth_url,
                                     username=CONF.openstack.os_username,
                                     password=CONF.openstack.os_password,
                                     tenant_name=CONF.openstack.
                                                      os_project_name)


def get_auth_v3():
    return keystone_v3_auth.Password(auth_url=CONF.openstack.os_auth_url,
                                     username=CONF.openstack.os_username,
                                     password=CONF.openstack.os_password,
                                     project_name=CONF.openstack.
                                                       os_project_name,
                                     project_domain_name=CONF.openstack.
                                                        os_project_domain_name,
                                     user_domain_name=CONF.
                                                openstack.os_user_domain_name)


def get_keystone_session():
    if CONF.openstack.os_auth_version == '2.0':
        return keystone_session.Session(auth=get_auth_v2())
    elif CONF.openstack.os_auth_version == '3':
        return keystone_session.Session(auth=get_auth_v3())
    else:
        LOG.error("Supports auth_version 2.0 and 3 only")
