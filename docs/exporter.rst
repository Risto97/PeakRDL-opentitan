Exporter
========

The exporter translates the compiled SystemRDL object model into an OpenTitan hjson
document.

The exporter will translate a given AddrmapNode object into an OpenTitan hjson dictionary
that contains a single that does not contain additional IP blocks inside.


API
---

.. autoclass:: peakrdl_opentitan.OpenTitanExporter
    :special-members: __init__
    :members: export

Limitations
-----------

Unfortunately, not all SystemRDL concepts are able to be faithfully translated
into OpenTitan hjson.
The warning is supposed to be printed whenever such property is encountered in SystemRDL.

* SystemRDL describes a vast amount of properties that have no equivalents in
  the OpenTitan standard, so unfortunately they are discarded.
