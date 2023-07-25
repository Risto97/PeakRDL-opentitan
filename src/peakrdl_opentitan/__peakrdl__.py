from typing import TYPE_CHECKING
import re

from peakrdl.plugins.importer import ImporterPlugin #pylint: disable=import-error
from peakrdl.plugins.exporter import ExporterSubcommandPlugin #pylint: disable=import-error

from .exporter import OpenTitanExporter
from .importer import OpenTitanImporter

if TYPE_CHECKING:
    import argparse
    from systemrdl import RDLCompiler
    from systemrdl.node import AddrmapNode


class Exporter(ExporterSubcommandPlugin):
    short_desc = "Export the register model to OpenTitan hwjson"

    def do_export(self, top_node: 'AddrmapNode', options: 'argparse.Namespace') -> None:

        x = OpenTitanExporter()
        x.export(
            top_node,
            options.output,
            # component_name=options.name
        )


class Importer(ImporterPlugin):
    file_extensions = ["hjson"]

    def is_compatible(self, path: str) -> bool:
        # Can be any hjson file.
        # No good way to test if it is Opentitan regtool format
        return True

    def add_importer_arguments(self, arg_group: 'argparse.ArgumentParser') -> None:
        pass

    def do_import(self, rdlc: 'RDLCompiler', options: 'argparse.Namespace', path: str) -> None:
        i = OpenTitanImporter(rdlc)
        i.import_file(
            path,
        )
