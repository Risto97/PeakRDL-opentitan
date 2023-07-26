Importer
========

Importing OpenTitan hjson definitions can occur at any point alongside normal SystemRDL
file compilation. When an OpenTitana hjson file is imported, the register description is
loaded into the SystemRDL register model as if it were an ``addrmap`` component
declaration. Once imported, the OpenTitan hjson contents can be used as-is, or
referenced from another RDL file.

Since the target register used internally uses SystemRDL semantics, the import
operation does a 'best effort' attempt to faithfully map the concepts described
in OpenTitan hjson into SystemRDL objects.

Some of the properties in OpenTitan hjson do not exist in SystemRDL, and vice versa.
In those cases a warning is printed during conversion and/or a sane conversion value is assumed.


Field swaccess and hwaccess fields
----------------------------------

SystemRDL supports more sw and hw access properties than OpenTitan format.
OpenTitan uses swaccess string property to describe the effect of software access to a field,
to get the wanted behaviour in SystemRDL it is neccessary to use sw, onread, onwrite properties additionally.
The table is shown next.

.. csv-table:: OpenTitan to SystemRDL swaccess properties
   :file: swaccess.csv
   :widths: 10 25 10 25 25 25
   :header-rows: 1

.. csv-table:: OpenTitan to SystemRDL hwaccess properties
   :file: hwaccess.csv
   :widths: 10 25 10
   :header-rows: 1

API
---

.. autoclass:: peakrdl_opentitan.OpenTitanImporter
    :special-members: __init__
    :members: import_file

Limitations
-----------

Unfortunately, not all OpenTitan hjson concepts are able to be faithfully translated
into SystemRDL.
The warning is supposed to be printed whenever such property is encountered in OpenTitan hjson.
