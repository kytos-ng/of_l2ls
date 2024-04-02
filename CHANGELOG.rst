#########
Changelog
#########
All notable changes to the ``of_l2ls`` project will be documented in this file.

[UNRELEASED] - Under development
********************************
Added
=====

Changed
=======
- Updated python environment installation from 3.9 to 3.11
- Updated test dependencies

Deprecated
==========

Removed
=======

Fixed
=====

Security
========

[1.2.1] - 2021-01-07
********************
Added
=====
- Added NApp requirements and Kytos Events to ``README.rst``

Fixed
=====
- Added ``table_id`` field required by consistency check in flows.


[1.2.0] - 2020-12-23
********************
Changed
=======
- Install and remove LLDP flows through the ``flow_manager`` NApp.
- Do not send packets if `OFPPC_NO_FWD` is set on the interface.
- Changed setup.py to alert when a test fails on Travis. 


[1.1.2] - 2020-07-23
********************
Added
=====
- Added unit tests: from 0% to 98%
- Added tags decorator to run tests by type and size.
- Added support for automated tests and CI with Travis.

Changed
=======
- Changed tests structure to separate unit and integration tests.
- Changed README.rst to include some info badges.

Fixed
=====
- Fixed Scrutinizer coverage error.


[1.1.1] - 2019-03-15
********************
Added
=====
- Continuous integration enabled at scrutinizer.

Fixed
=====
- Fixed some linter issues.

[1.1.0] - 2018-06-15
********************
Added
=====
- Added support to use OpenFlow 1.3.

Changed
=======
- Ignore LLDP packages.
- Updating kytos and python-openflow requirements versions.
- Only use buffer_id in packet_out.

Fixed
=====
- Fixed Ghost hosts appearing in web interface.

[1.0.0] - 2017-05-05
********************
Changed
=======
- Installation process of NApps.
- Logging updated to match changes on Kytos project.

Deprecated
==========
- 'author' attribute was renamed to 'username', and will be removed in future
  releases.

Fixed
=====
- Several bug fixes.


[0.2.0] - 2017-03-24
********************
Added
=====
- Python3.6 requirement.
- Individual Settings file.


[0.1.0] - 2016-11-09
********************
Added
=====
- kytos.json file with NApp metadata.
- LICENSE file.
- First version of the NApp.

