"""NApp responsible for the main OpenFlow basic operations."""

from kytos.core import log
from kytos.core.events import KytosEvent
from kytos.core.flow import Flow
from kytos.core.helpers import listen_to
from kytos.core.napps import KytosNApp
from kytos.core.switch import Interface
from pyof.v0x01.common.utils import new_message_from_header
from pyof.v0x01.asynchronous.error_msg import ErrorMsg
from pyof.v0x01.asynchronous.error_msg import ErrorType, HelloFailedCode
from pyof.v0x01.controller2switch.common import FlowStatsRequest
from pyof.v0x01.controller2switch.features_request import FeaturesRequest
from pyof.v0x01.controller2switch.stats_request import StatsRequest, StatsTypes
from pyof.v0x01.symmetric.echo_reply import EchoReply
from pyof.v0x01.symmetric.hello import Hello

from napps.kytos.of_core import settings


class Main(KytosNApp):
    """Main class of the NApp responsible for OpenFlow basic operations."""

    def setup(self):
        """App initialization (used instead of ``__init__``).

        The setup method is automatically called by the run method.
        Users shouldn't call this method directly.
        """
        self.name = 'kytos/of_core'
        self.execute_as_loop(settings.STATS_INTERVAL)

    def execute(self):
        """Method to be runned once on app 'start' or in a loop.

        The execute method is called by the run method of KytosNApp class.
        Users shouldn't call this method directly.
        """
        for switch in self.controller.switches.values():
            self._update_flow_list(switch)

    def _update_flow_list(self, switch):
        """Method responsible for request stats of flow to switches.

        Args:
            switch(:class:`~kytos.core.switch.Switch`):
                target to send a stats request.
        """
        body = FlowStatsRequest()  # Port.OFPP_NONE and All Tables
        req = StatsRequest(body_type=StatsTypes.OFPST_FLOW, body=body)
        req.pack()
        event = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_stats_request',
            content={'message': req, 'destination': switch.connection})
        self.controller.buffers.msg_out.put(event)

    @staticmethod
    @listen_to('kytos/of_core.messages.in.ofpt_stats_reply')
    def handle_flow_stats_reply(event):
        """Handle flow stats reply message.

        This method updates the switches list with its Flow Stats.

        Args:
            event (:class:`~kytos.core.events.KytosEvent):
                Event with ofpt_stats_reply in message.
        """
        msg = event.content['message']
        if msg.body_type == StatsTypes.OFPST_FLOW:
            switch = event.source.switch
            flows = []
            for flow_stat in msg.body:
                new_flow = Flow.from_flow_stats(flow_stat)
                flows.append(new_flow)
            switch.flows = flows

    @listen_to('kytos/of_core.messages.in.ofpt_features_reply')
    def handle_features_reply(self, event):
        """Handle received kytos/of_core.messages.in.ofpt_features_reply event.

        Reads the KytosEvent with features reply message sent by the client,
        save this data and sends three new messages to the client:

            * SetConfig Message;
            * FlowMod Message with a FlowDelete command;
            * BarrierRequest Message;

        This is the end of the Handshake workflow of the OpenFlow Protocol.

        Args:
            event (KytosEvent): Event with features reply message.
        """
        log.debug('Handling Features Reply Event')

        features = event.content['message']
        dpid = features.datapath_id.value

        switch = self.controller.get_switch_or_create(dpid=dpid,
                                                      connection=event.source)

        for port in features.ports:
            interface = Interface(name=port.name.value,
                                  address=port.hw_addr.value,
                                  port_number=port.port_no.value,
                                  switch=switch,
                                  state=port.state.value,
                                  features=port.curr)
            switch.update_interface(interface)

        switch.update_features(features)

    @listen_to('kytos/core.messages.openflow.new')
    def handle_new_openflow_message(self, event):
        """Handle a RawEvent and generate a kytos/core.messages.in.* event.

        Args:
            event (KytosEvent): RawEvent with openflow message to be unpacked
        """
        log.debug('RawOpenFlowMessage received by RawOFMessage handler')

        # creates an empty OpenFlow Message based on the message_type defined
        # on the unpacked header.
        message = new_message_from_header(event.content['header'])
        binary_data = event.content['binary_data']

        # The unpack will happen only to those messages with body beyond header
        if binary_data and len(binary_data) > 0:
            message.unpack(binary_data)
        log.debug('RawOpenFlowMessage unpacked')

        name = message.header.message_type.name.lower()
        of_event = KytosEvent(name="kytos/of_core.messages.in.{}".format(name),
                              content={'message': message,
                                       'source': event.source})
        self.controller.buffers.msg_in.put(of_event)

    @listen_to('kytos/of_core.messages.in.ofpt_echo_request')
    def handle_echo_request(self, event):
        """Handle Echo Request Messages.

        This method will get a echo request sent by client and generate a
        echo reply as answer.

        Args:
            event (:class:`~kytos.core.events.KytosEvent`):
                Event with echo request in message.
        """
        log.debug("Echo Request message read")

        echo_request = event.message
        echo_reply = EchoReply(xid=echo_request.header.xid)
        event_out = KytosEvent(name=('kytos/of_core.messages.out.'
                                     'ofpt_echo_reply'),
                               content={'message': echo_reply,
                                        'destination': event.source})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/core.connection.new')
    def handle_core_new_connection(self, event):
        self.say_hello(event.source)

    def say_hello(self, destination, xid=None):
        # should be called once a new connection is established.
        # To be able to deal with of1.3 negotiation, hello should also
        # cary a version_bitmap.
        hello = Hello(xid=xid)
        event_out = KytosEvent(
            name='kytos/of_core.messages.out.ofpt_hello',
            content={'message': hello,
                     'destination': destination})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of_core.messages.in.ofpt_hello')
    def handle_openflow_in_hello(self, event):
        """Handle hello messages.

        This method will get a KytosEvent with hello message sent by client
        and deal with negotiation.

        Args:
            event (KytosMessageInHello): KytosMessageInHelloEvent
        """
        log.debug('Handling kytos/of_core.messages.in.ofpt_hello')

        # checking if version is 1.0 or later for now.
        # TODO: should check for version_bitmap on hello message for proper
        # negotiation.
        if event.message.header.version >= 0x01:
            event_raw = KytosEvent(
                name='kytos/of_core.hello_complete',
                content={'destination': event.source})
            self.controller.buffers.raw.put(event_raw)
        else:
            error_message = ErrorMsg(xid=event.message.header.xid,
                                     error_type=ErrorType.OFPET_HELLO_FAILED,
                                     code=HelloFailedCode.OFPHFC_INCOMPATIBLE)
            event_out = KytosEvent(
                name='kytos/of_core.messages.out.hello_failed',
                content={'source': event.destination,
                         'destination': event.source,
                         'message': error_message})
            self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of_core.messages.out.ofpt_echo_reply')
    def handle_queued_openflow_echo_reply(self, event):
        if settings.SEND_FEATURES_REQUEST_ON_ECHO:
            self.send_features_request(event.destination)

    @listen_to('kytos/of_core.hello_complete')
    def handle_openflow_hello_complete(self, event):
        self.send_features_request(event.destination)

    def send_features_request(self, destination):
        """Send a feature request to the switch."""
        log.debug('Sending a feature request after responding to a hello')

        event_out = KytosEvent(name=('kytos/of_core.messages.out.'
                                     'ofpt_features_request'),
                               content={'message': FeaturesRequest(),
                                        'destination': destination})
        self.controller.buffers.msg_out.put(event_out)

    @listen_to('kytos/of_core.messages.in.hello_failed',
               'kytos/of_core.messages.out.hello_failed')
    # may present concurrency issues due to unordered
    # event listeners call. sugestion:
    # listen to 'kytos/of_core.hello_failed', trigered when message is sent)
    def handle_openflow_in_hello_failed(self, event):
        # terminate the connection
        # but should do it only after the message has been sent...
        # not in concurrency with the sender method
        event.destination.close()

    def shutdown(self):
        """End of the application."""
        log.debug('Shutting down...')
