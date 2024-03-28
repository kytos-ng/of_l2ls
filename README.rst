########
Overview
########

**WARNING: As previously announced on our communication channels, the Kytos
project will enter the "shutdown" phase on May 31, 2021. After this date,
only critical patches (security and core bug fixes) will be accepted, and the
project will be in "critical-only" mode for another six months (until November
30, 2021). For more information visit the FAQ at <https://kytos.io/faq>. We'll
have eternal gratitude to the entire community of developers and users that made
the project so far.**

|License| |Build| |Coverage| |Quality|

The **of_l2ls** application is used in basic operation of switches. It
implements the algorithm known as L2 Learning Switch, which aims to figure out
which host is attached to which switch port. The switch keeps a table that
stores a tuple containing the mac address (hardware address) and port number.
So, the switch can forward the packets directly to the destination host.
Initially this table is empty, so the first step, when a host tries to send a
packet to another host, is to add an entry pointing to the source host. Next,
the switch sends the packet to all ports, except to the port of the source
host. The destination host will answer to that packet and once the packet is
received, the switch adds an entry to the table mapping the mac address of the
destination host to a port. This process is repeated until all ports with a
host connected are mapped. This algorithm can be used to update the table when
a change is detected.

**********
Installing
**********

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/kytos-ng/of_l2ls.git
   $ cd of_l2ls
   $ python3 -m pip install --editable .

To install the kytos environment, please follow our
`development environment setup <https://github.com/kytos-ng/documentation/blob/master/tutorials/napps/development_environment_setup.rst>`_.

************
Requirements
************

- kytos/flow_manager
- kytos/of_core
- kytos/topology

********
Advanced
********

L2 Learning Switch Operation
============================

At the switch startup, it does not know which hosts are attached to its ports.
So, when some host A sends a frame addressed to host B, the switch will
broadcast this frame to all ports, except to the port from where the frame has
arrived. At same time, the switch learns at which port host A is attached. A
table is stored in switch's local memory mapping the host mac address and port
number.

When the host B answers the request, the switch adds to this table an entry
mapping the mac address of host B to the port in which it is connected. This
process goes on until the switch learns which port all hosts are connected.

######
Events
######

********
Listened
********

kytos/topology.switch.(enabled|disabled)
========================================
Listen when a switch was enabled or disabled.

Content
-------

.. code-block:: python3

   {
     'dpid': <switch.id>
   }

kytos/of_core.v0x0[14].messages.in.ofpt_packet_in
=================================================
Listen PacketIn Event.

Content
-------

.. code-block:: python3

    {
      'message': <object>, # instance of python-openflow PacketIn message
      'source': <object> # instance of kytos.core.switch.Connection class
    }

*********
Generated
*********

kytos/of_l2ls.messages.out.ofpt_packet_out
==========================================
Standard "message out" event with a PacketOut message to the switch containing
a of_l2ls packet inside it.

Content
-------

.. code-block:: python3

    {
      'message': <object>, # instance of python-openflow PacketOut message
      'source': <object> # instance of kytos.core.switch.Connection class
    }

.. TAGs

.. |License| image:: https://img.shields.io/github/license/kytos/kytos.svg
   :target: https://github.com/kytos/of_l2ls/blob/master/LICENSE
.. |Build| image:: https://scrutinizer-ci.com/g/kytos/of_l2ls/badges/build.png?b=master
  :alt: Build status
  :target: https://scrutinizer-ci.com/g/kytos/of_l2ls/?branch=master
.. |Coverage| image:: https://scrutinizer-ci.com/g/kytos/of_l2ls/badges/coverage.png?b=master
  :alt: Code coverage
  :target: https://scrutinizer-ci.com/g/kytos/of_l2ls/?branch=master
.. |Quality| image:: https://scrutinizer-ci.com/g/kytos/of_l2ls/badges/quality-score.png?b=master
  :alt: Code-quality score
  :target: https://scrutinizer-ci.com/g/kytos/of_l2ls/?branch=master