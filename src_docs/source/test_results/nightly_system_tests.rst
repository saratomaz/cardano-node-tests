Nightly system tests pipelines
==============================

These Cardano node system tests are run on a nightly basis. The tests are run on multiple instances of a local cluster.
The tests are run on the `master` branch of the `cardano-node` repository.

Several pipelines run the nightly system tests. In each pipeline, different sets of tests are run.


Test statuses
-------------

* **failed** - tests that failed assertion or that were aborted because of unhandled exception
* **broken** - tests that are affected by a real known issue; these are marked as `xfailed` (expected failure) until the issue is fixed
* **skipped** - tests that are not meant to run in the given pipeline


Nightly results
---------------

`Results on Github Actions <https://github.com/IntersectMBO/cardano-node-tests/actions?query=workflow%3A%22Nightly+tests%22+event%3Aschedule+branch%3Amaster++>`__

* `nightly <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly/>`__:  |nightly-badge|
   * network in Babbage era
   * default transaction era
   * mixed network topology (two stake pools P2P, two stake pools default topology)
* `nightly-dbsync <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-dbsync/>`__:  |nightly-dbsync-badge|
   * network in Babbage era
   * Babbage transaction era
   * default (legacy) network topology
   * DB Sync testing enabled
* `nightly-p2p <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-p2p/>`__:  |nightly-p2p-badge|
   * network in Babbage era
   * Babbage transaction era
   * P2P network topology
   * cluster starts directly in Babbage era
* `nightly-conway-cc <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-cc/>`__:  |nightly-conway-cc-badge|
   * network in Conway era
   * protocol version 10
   * P2P network topology
   * Constitutional Commitee has 3 members
   * cluster starts directly in Conway era
* `nightly-conway-bootstrap <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-bootstrap/>`__:  |nightly-conway-bootstrap-badge|
   * network in Conway era
   * protocol version 9 (bootstrap phase)
   * P2P network topology
   * Constitutional Commitee has 3 members
   * cluster starts directly in Conway era
* `nightly-conway-no-cc <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-no-cc/>`__:  |nightly-conway-nocc-badge|
   * network in Conway era
   * protocol version 10
   * P2P network topology
   * Constitutional Commitee has 0 members
   * cluster starts directly in Conway era

Nightly upgrade testing
^^^^^^^^^^^^^^^^^^^^^^^

* `Step 1 <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step1/>`__:  |nightly-upgrade-step1-badge|
   * use the `latest cardano-node release <https://github.com/IntersectMBO/cardano-node-tests/blob/master/.github/env_nightly_upgrade>`__ for Mainnet
   * network in Babbage era
   * Babbage transaction era
   * default (legacy) network topology
   * smoke tests
* `Step 2 <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step2/>`__:  |nightly-upgrade-step2-badge|
   * upgrade all nodes except one to latest cardano-node master
   * network in Babbage era
   * Babbage transaction era
   * mixed network topology (half nodes P2P, half nodes legacy topology)
   * smoke tests
* `Step 3 <https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step3/>`__:  |nightly-upgrade-step3-badge|
   * upgrade the last remaining node to latest cardano-node master
   * network in Babbage era
   * Babbage transaction era
   * P2P network topology
   * smoke tests

.. |nightly-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly/

.. |nightly-dbsync-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-dbsync%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-dbsync/

.. |nightly-p2p-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-p2p%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-p2p/

.. |nightly-upgrade-step1-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-upgrade%2Fstep1%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step1/

.. |nightly-upgrade-step2-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-upgrade%2Fstep2%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step2/

.. |nightly-upgrade-step3-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-upgrade%2Fstep3%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-upgrade/step3/

.. |nightly-conway-cc-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-conway-cc%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-cc/

.. |nightly-conway-bootstrap-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-conway-bootstrap%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-bootstrap/

.. |nightly-conway-nocc-badge| image:: https://img.shields.io/endpoint?url=https%3A%2F%2Fcardano-tests-reports-3-74-115-22.nip.io%2Fcardano-node-tests-nightly-conway-no-cc%2Fbadge.json
   :target: https://cardano-tests-reports-3-74-115-22.nip.io/cardano-node-tests-nightly-conway-no-cc/
