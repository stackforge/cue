# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Authors: Davide Agnello <davide.agnello@hp.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Copyright [2014] Hewlett-Packard Development Company, L.P.
# limitations under the License.

"""Version 1 of the Cue API
"""
import uuid

from cue.api.controllers import base
from cue.common import exception
from cue.common.i18n import _  # noqa
from cue.common.i18n import _LI  # noqa
from cue import objects
from cue.openstack.common import log as logging
from cue.taskflow import client as task_flow_client
from cue.taskflow.flow import create_cluster
from cue.taskflow.flow import delete_cluster

from oslo.utils import uuidutils
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

LOG = logging.getLogger(__name__)


class EndPoint(base.APIBase):
    """Representation of an End point."""

    def __init__(self, **kwargs):
        self.fields = []
        endpoint_object_fields = list(objects.Endpoint.fields)
        for k in endpoint_object_fields:
            # only add fields we expose in the api
            if hasattr(self, k):
                self.fields.append(k)
                setattr(self, k, kwargs.get(k, wtypes.Unset))

    type = wtypes.text
    "type of endpoint"

    uri = wtypes.text
    "URL to endpoint"


class ClusterDetails(base.APIBase):
    """Representation of a cluster's details."""
    # todo(dagnello): WSME attribute verification sometimes triggers 500 server
    # error when user input was actually invalid (400).  Example: if 'size' was
    # provided as a string/char, e.g. 'a', api returns 500 server error.

    def __init__(self, **kwargs):
        self.fields = []
        cluster_object_fields = list(objects.Cluster.fields)
        # Adding nodes since it is an api-only attribute.
        self.fields.append('nodes')
        for k in cluster_object_fields:
            # only add fields we expose in the api
            if hasattr(self, k):
                self.fields.append(k)
                setattr(self, k, kwargs.get(k, wtypes.Unset))

    id = wtypes.text
    "UUID of cluster"

    network_id = wtypes.wsattr(wtypes.text, mandatory=True)
    "NIC of Neutron network"

    name = wsme.wsattr(wtypes.text, mandatory=True)
    "Name of cluster"

    status = wtypes.text
    "Current status of cluster"

    flavor = wsme.wsattr(wtypes.text, mandatory=True)
    "Flavor of cluster"

    size = wtypes.IntegerType()
    "Number of nodes in cluster"

    volume_size = wtypes.IntegerType()
    "Volume size for nodes in cluster"

    end_points = wtypes.wsattr([EndPoint], default=[])
    "List of endpoints on accessing node"


class Cluster(base.APIBase):
    """API representation of a cluster."""

    cluster = ClusterDetails

    def __init__(self, **kwargs):
        self._type = 'cluster'


class ClusterCollection(base.APIBase):
    """API representation of a collection of clusters."""

    clusters = [ClusterDetails]
    """A list containing Cluster objects"""

    def __init__(self, **kwargs):
        self._type = 'clusters'


def get_complete_cluster(context, cluster_id):
    """Helper to retrieve the api-compatible full structure of a cluster."""

    cluster_obj = objects.Cluster.get_cluster_by_id(context, cluster_id)

    # construct api cluster object
    cluster = ClusterDetails(**cluster_obj.as_dict())

    cluster_nodes = objects.Node.get_nodes_by_cluster_id(context, cluster_id)

    for node in cluster_nodes:
        # extract endpoints from node
        node_endpoints = objects.Endpoint.get_endpoints_by_node_id(context,
                                                                   node.id)

        # construct api endpoint objects
        cluster.end_points = [EndPoint(**obj_endpoint.as_dict()) for
                              obj_endpoint in node_endpoints]

    return cluster


class ClusterController(rest.RestController):
    """Manages operations on specific Cluster of nodes."""

    def __init__(self, cluster_id):
        self.id = cluster_id

    @wsme_pecan.wsexpose(Cluster, status_code=200)
    def get(self):
        """Return this cluster."""
        context = pecan.request.context
        cluster = Cluster()
        cluster.cluster = get_complete_cluster(context, self.id)

        return cluster

    @wsme_pecan.wsexpose(None, status_code=202)
    def delete(self):
        """Delete this Cluster."""
        context = pecan.request.context

        # update cluster to deleting
        objects.Cluster.update_cluster_deleting(context, self.id)

        # prepare and post cluster delete job to backend
        job_args = {
            "cluster_id": self.id,
            "cluster_status": "deleting",
        }
        job_client = task_flow_client.get_client_instance()
        job_uuid = uuidutils.generate_uuid()
        job_client.post(delete_cluster, job_args, tx_uuid=job_uuid)

        msg_params = {
            "cluster_id": self.id,
            "job_id": job_uuid,
        }
        log_message = _LI('Delete Cluster Request:\n Cluster ID: {cluster_id}'
                          '\n Job ID: {job_id}')
        LOG.info(log_message.format(**msg_params))


class ClustersController(rest.RestController):
    """Manages operations on Clusters of nodes."""

    @wsme_pecan.wsexpose(ClusterCollection, status_code=200)
    def get(self):
        """Return list of Clusters."""

        context = pecan.request.context
        clusters = objects.Cluster.get_clusters(context)
        cluster_list = ClusterCollection()
        cluster_list.clusters = [ClusterDetails(**obj_cluster.as_dict())
                                 for obj_cluster in clusters]

        return cluster_list

    @wsme_pecan.wsexpose(Cluster, body=ClusterDetails, status_code=202)
    def post(self, data):
        """Create a new Cluster.

        :param data: cluster parameters within the request body.
        """
        context = pecan.request.context

        if data.size <= 0:
            raise exception.Invalid(_("Invalid cluster size provided"))

        # create new cluster object with required data from user
        new_cluster = objects.Cluster(**data.as_dict())

        # create new cluster with node related data from user
        new_cluster.create(context)

        # retrieve cluster data
        cluster = Cluster()
        cluster.cluster = get_complete_cluster(context, new_cluster.id)

        # prepare and post cluster create job to backend
        job_args = {
            "size": cluster.cluster.size,
            "flavor": cluster.cluster.flavor,
            "volume_size": cluster.cluster.volume_size,
            "network_id": cluster.cluster.network_id,
            "cluster_status": "BUILDING",
            "node_id": "node_id",
            "port_name": "port_" + str(uuid.uuid4()),
        }
        job_client = task_flow_client.get_client_instance()
        job_uuid = uuidutils.generate_uuid()
        job_client.post(create_cluster, job_args, tx_uuid=job_uuid)

        msg_params = {
            "cluster_id": cluster.cluster.id,
            "size": cluster.cluster.size,
            "network_id": cluster.cluster.network_id,
            "job_id": job_uuid,
        }
        log_message = _LI('Create Cluster Request:\n Cluster ID: {cluster_id}'
                          '\n Cluster size: {size}\n network ID: '
                          '{network_id}\n Job ID: {job_id}')
        LOG.info(log_message.format(**msg_params))

        return cluster

    @pecan.expose()
    def _lookup(self, cluster_id, *remainder):
        return ClusterController(cluster_id), remainder


class V1Controller(object):
    """Version 1 MSGaaS API controller root."""
    clusters = ClustersController()
