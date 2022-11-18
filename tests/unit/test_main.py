"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import pytest
from kytos.lib.helpers import (get_controller_mock, get_kytos_event_mock,
                               get_switch_mock)
from pyof.v0x04.common.port import PortConfig as PortConfig13


# pylint: disable=protected-access
class TestMain(TestCase):
    """Tests for the Main class."""

    def setUp(self):
        """Execute steps before each tests."""
        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_l2ls.main import Main
        self.addCleanup(patch.stopall)

        self.napp = Main(get_controller_mock())

    @patch('napps.kytos.of_l2ls.main.Port13')
    @patch('napps.kytos.of_l2ls.main.requests')
    @patch('napps.kytos.of_l2ls.main.settings')
    @patch('kytos.core.controller.Controller.get_switch_by_dpid')
    def test_install_table_miss_flow(self, *args):
        """Test _create_flow_mod method for flow 1.3 packet."""
        (mock_get_switch_by_dpid, mock_settings, mock_requests,
         mock_port13) = args

        mock_port13.OFPP_CONTROLLER = 123
        flow_manager_url = 'http://localhost:8181/api/kytos/flow_manager/v2'

        mock_settings.FLOW_MANAGER_URL = flow_manager_url
        mock_settings.TABLE_ID = 0
        expected_flow = {}
        expected_flow['priority'] = 0
        expected_flow['table_id'] = 0
        expected_flow['actions'] = [{'action_type': 'output',
                                     'port': 123}]

        dpid = "00:00:00:00:00:00:00:01"
        switch = get_switch_mock(dpid, 0x04)
        mock_get_switch_by_dpid.return_value = switch

        destination = switch.id
        endpoint = f'{flow_manager_url}/flows/{destination}'

        event = get_kytos_event_mock(name='kytos/topology.switch.enabled',
                                     content={'dpid': dpid})
        self.napp.install_table_miss_flow(event)

        data = {'flows': [expected_flow]}
        mock_requests.post.assert_called_with(endpoint, json=data)

    @patch('napps.kytos.of_l2ls.main.settings')
    def test_create_flow(self, mock_settings):
        """Test _create_flow method."""

        expected_flow = {}
        match = {}

        expected_flow['priority'] = 10
        expected_flow['table_id'] = 0

        match['dl_src'] = '00:00:00:00:00:00:00:01'
        match['dl_dst'] = '00:00:00:00:00:00:00:02'
        match['dl_type'] = 0x800

        expected_flow['match'] = match
        expected_flow['actions'] = [{'action_type': 'output',
                                     'port': 123}]
        mock_settings.FLOW_PRIORITY = 10
        mock_settings.TABLE_ID = 0

        packet = MagicMock()
        packet.source.value = '00:00:00:00:00:00:00:01'
        packet.destination.value = '00:00:00:00:00:00:00:02'
        packet.ether_type.value = 0x800

        flow_out = self.napp._create_flow(packet, 123)

        self.assertDictEqual(expected_flow, flow_out)

    @patch('napps.kytos.of_l2ls.main.Output13')
    @patch('napps.kytos.of_l2ls.main.PacketOut13')
    def test_create_packet_out_13(self, *args):
        """Test _create_packet_out method for packet_out 1.3 packet."""
        (mock_packet_out, mock_action) = args

        packet_out = MagicMock()
        packet_out.actions = []
        action = MagicMock()
        switch = MagicMock()

        mock_packet_out.return_value = packet_out
        mock_action.return_value = action

        packet = MagicMock()
        packet.buffer_id = 2
        packet.in_port = 2
        packet.data = '2'
        packet_out = self.napp._create_packet_out('0x04', packet, [], switch)

        self.assertEqual(packet_out.actions[0], action)
        self.assertEqual(packet_out.buffer_id, packet.buffer_id)
        self.assertEqual(packet_out.in_port, packet.in_port)
        self.assertEqual(packet_out.data, packet.data)

    def test_create_packet_out_13__none(self):
        """Test _create_packet_out method for packet_out 1.3 packet when
           interface is OFPPC_NO_FWD.
        """
        packet = MagicMock()
        iface = MagicMock()
        iface.config = PortConfig13.OFPPC_NO_FWD
        switch = MagicMock()
        switch.interfaces = {1: iface}
        switch.get_interface_by_port_no.return_value = iface

        packet_out = self.napp._create_packet_out('0x04', packet, [1], switch)

        self.assertIsNone(packet_out)

    @pytest.mark.xfail
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.of_l2ls.main.Main._create_packet_out')
    @patch('napps.kytos.of_l2ls.main.Main._create_flow')
    @patch('napps.kytos.of_l2ls.main.KytosEvent')
    @patch('napps.kytos.of_l2ls.main.Ethernet')
    @patch('napps.kytos.of_l2ls.main.requests')
    def test_handle_packet_in(self, *args):
        """Test handle_packet_in method."""
        (mock_requests, mock_ethernet, mock_kytos_event, mock_create_flow,
         mock_create_packet_out, mock_buffer_put) = args

        ethernet = MagicMock()
        mock_ethernet.return_value = ethernet

        flow_dict = MagicMock()
        mock_create_flow.return_value = flow_dict

        packet_out = MagicMock()
        mock_create_packet_out.return_value = packet_out

        ports = [1, 2]
        switch = get_switch_mock("00:00:00:00:00:00:00:01", 0x04)
        switch.where_is_mac.return_value = ports
        message = MagicMock()
        message.reason = 0
        message.in_port = 1
        event = get_kytos_event_mock(name='kytos/of_core.v0x0[4].messages.in.'
                                          'ofpt_packet_in',
                                     content={'source': switch.connection,
                                              'message': message})

        self.napp.handle_packet_in(event)

        switch.update_mac_table.assert_called_with(ethernet.source,
                                                   message.in_port)

        mock_create_flow.assert_called_with(ethernet, ports[0])
        mock_create_packet_out.assert_called_with(switch.ofp_version,
                                                  message, ports, switch)

        event_call = [call(name='kytos/of_l2ls.messages.out.ofpt_packet_out',
                           content={'destination': event.source,
                                    'message': packet_out})]

        mock_kytos_event.assert_has_calls(event_call)

        self.assertEqual(mock_requests.post.call_count, 1)
        self.assertEqual(mock_buffer_put.call_count, 1)
