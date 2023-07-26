#### SystemRDL <-> Opentitan regblock HWjson description importer exporter

These 2 formats solve a similar problem, aim of the tool is to provide a tool to easily migrate from one format to another and hopefully reuse PeakRDL toolchain for opentitan peripherals, also use SystemRDL IP blocks with opentitan tools.

At the moment there is a basic exporter and importer implemented.

Some features are unsupported at the moment but they can be supported. While some features are incompatible between the two formats.

# PeakRDL-opentitan
This package implements OpenTitan hjson import and export for the PeakRDL toolchain.

- **Export:** Convert compiled SystemRDL input into OpenTitan regtool hjson
- **Import:** Read an OpenTitan regtool hjson file and import it into the `systemrdl-compiler` namespace, or write to SystemRDL file

For the command line tool, see the [PeakRDL project](https://peakrdl.readthedocs.io).

## Documentation
See the [PeakRDL-opentitan Documentation]() for more details
