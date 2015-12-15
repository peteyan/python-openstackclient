#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""Router action implementations"""

import json
import logging

from cliff import lister
from cliff import show

from openstackclient.common import utils
from openstackclient.identity import common as identity_common


def _format_admin_state(state):
    return 'UP' if state else 'DOWN'


def _format_external_gateway_info(info):
    try:
        return json.dumps(info)
    except (TypeError, KeyError):
        return ''


_formatters = {
    'admin_state_up': _format_admin_state,
    'external_gateway_info': _format_external_gateway_info,
}


def _get_attrs(client_manager, parsed_args):
    attrs = {}
    if parsed_args.name is not None:
        attrs['name'] = str(parsed_args.name)
    if parsed_args.admin_state_up is not None:
        attrs['admin_state_up'] = parsed_args.admin_state_up
    if parsed_args.distributed is not None:
        attrs['distributed'] = parsed_args.distributed
    if 'project' in parsed_args and parsed_args.project is not None:
        identity_client = client_manager.identity
        project_id = identity_common.find_project(
            identity_client,
            parsed_args.project,
            parsed_args.project_domain,
        ).id
        attrs['tenant_id'] = project_id
    return attrs


class CreateRouter(show.ShowOne):
    """Create a new router"""

    log = logging.getLogger(__name__ + '.CreateRouter')

    def get_parser(self, prog_name):
        parser = super(CreateRouter, self).get_parser(prog_name)
        parser.add_argument(
            'name',
            metavar='<name>',
            help="New router name",
        )
        admin_group = parser.add_mutually_exclusive_group()
        admin_group.add_argument(
            '--enable',
            dest='admin_state_up',
            action='store_true',
            default=True,
            help="Enable router (default)",
        )
        admin_group.add_argument(
            '--disable',
            dest='admin_state_up',
            action='store_false',
            help="Disable router",
        )
        parser.add_argument(
            '--distributed',
            dest='distributed',
            action='store_true',
            default=False,
            help="Create a distributed router",
        )
        parser.add_argument(
            '--project',
            metavar='<poroject>',
            help="Owner's project (name or ID)",
        )
        identity_common.add_project_domain_option_to_parser(parser)
        return parser

    def take_action(self, parsed_args):
        self.log.debug('take_action(%s)' % parsed_args)
        client = self.app.client_manager.network

        attrs = _get_attrs(self.app.client_manager, parsed_args)
        obj = client.create_router(**attrs)

        columns = sorted(obj.keys())
        data = utils.get_item_properties(obj, columns, formatters=_formatters)

        if 'tenant_id' in columns:
            # Rename "tenant_id" to "project_id".
            index = columns.index('tenant_id')
            columns[index] = 'project_id'
        return (tuple(columns), data)


class ListRouter(lister.Lister):
    """List routers"""

    log = logging.getLogger(__name__ + '.ListRouter')

    def get_parser(self, prog_name):
        parser = super(ListRouter, self).get_parser(prog_name)
        parser.add_argument(
            '--long',
            action='store_true',
            default=False,
            help='List additional fields in output',
        )
        return parser

    def take_action(self, parsed_args):
        self.log.debug('take_action(%s)' % parsed_args)
        client = self.app.client_manager.network

        columns = (
            'id',
            'name',
            'status',
            'admin_state_up',
            'distributed',
            'ha',
            'tenant_id',
        )
        column_headers = (
            'ID',
            'Name',
            'Status',
            'State',
            'Distributed',
            'HA',
            'Project',
        )
        if parsed_args.long:
            columns = columns + (
                'routes',
                'external_gateway_info',
            )
            column_headers = column_headers + (
                'Routes',
                'External gateway info',
            )

        data = client.routers()
        return (column_headers,
                (utils.get_item_properties(
                    s, columns,
                    formatters=_formatters,
                ) for s in data))