from typing import Union, TYPE_CHECKING, Any
import os

from systemrdl.node import RootNode
from systemrdl.node import AddrmapNode, MemNode
from systemrdl.node import RegNode, FieldNode

from .typemaps import sw_from_access, access_from_sw, hw_from_access, access_from_hw

if TYPE_CHECKING:
    from systemrdl.messages import MessageHandler

from typing import Any, TextIO

import hjson  # type: ignore


def gen_json(obj: Any, outfile: TextIO, format: str) -> None:
    if format == 'json':
        hjson.dumpJSON(obj,
                       outfile,
                       ensure_ascii=False,
                       use_decimal=True,
                       indent='  ',
                       for_json=True)
    elif format == 'compact':
        hjson.dumpJSON(obj,
                       outfile,
                       ensure_ascii=False,
                       for_json=True,
                       use_decimal=True,
                       separators=(',', ':'))
    elif format == 'hjson':
        hjson.dump(obj,
                   outfile,
                   ensure_ascii=False,
                   for_json=True,
                   use_decimal=True)
    else:
        raise ValueError('Invalid JSON format ' + format)
#===============================================================================
class OpenTitanExporter:
    def __init__(self, **kwargs: Any) -> None:

        # Check for stray kwargs
        if kwargs:
            raise TypeError("got an unexpected keyword argument '%s'" % list(kwargs.keys())[0])

    #---------------------------------------------------------------------------
    def export(self, node: Union[AddrmapNode, RootNode], outdir: str, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        node: AddrmapNode
            Top-level SystemRDL node to export.
        outdir:
            Output directory where to save the exported OpenTitan .hjson file.
        component_name: str
            HJson component name. If unspecified, uses the top node's name
            upon export.
        """

        self.msg = node.env.msg

        component_name = kwargs.pop("component_name", None) or node.inst_name

        # Check for stray kwargs
        if kwargs:
            raise TypeError("got an unexpected keyword argument '%s'" % list(kwargs.keys())[0])

        # If it is the root node, skip to top addrmap
        if isinstance(node, RootNode):
            node = node.top

        if not isinstance(node, (AddrmapNode, MemNode)):
            raise TypeError("'node' argument expects type AddrmapNode or MemNode. Got '%s'" % type(node).__name__)

        # Initialize HJSON
        self.doc = {}

        if not isinstance(node, AddrmapNode):
            raise TypeError("Expected Addrmap got: %s" % type(node).__name__)
        
        self.doc['name'] = node.orig_type_name
        self.doc['human_name'] = node.get_property("name")
        self.doc['one_paragraph_desc'] = node.get_property("desc")


        self.doc['clocking'] = []
        clocking = {}
        self.doc['available_inout_list'] = []
        self.doc['available_input_list'] = []
        self.doc['available_output_list'] = []
        for s in node.signals():
            signal_type = s.get_property("signal_type", default=False)
            if signal_type.name == "clk":
                clocking["clock"] = s.inst_name
            elif signal_type.name == "rst":
                clocking["reset"] = s.inst_name
            elif signal_type.name in ["input", "output", "inout"]:
                sig_dict = {'name': s.inst_name,
                         'width': s.width,
                         'desc': s.get_property("desc", default="")}
                self.doc[f"available_{signal_type.name}_list"].append(sig_dict)

        self.doc['clocking'].append(clocking)

        # self.doc['regwidth'] = TODO

        self.doc['registers'] = []
        for c in node.children():
            if isinstance(c, RegNode):
                self.doc['registers'].append(self.add_register(c))

        # TODO parse ifports, regtool only supports tilelink, so just add that
        self.doc['bus_interfaces'] = [{ "protocol" : "tlul", "direction": "device"}]
    
        print(outdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        with open(os.path.join(outdir, node.orig_type_name + ".hjson"), 'w') as f:
            gen_json(self.doc, f, "json")


    def add_register(self, reg : RegNode):
        regjson = {}

        regjson['name'] = reg.inst_name
        regjson['desc'] = reg.get_property("desc", default="")

        fields = []
        for c in reg.children():
            if isinstance(c, FieldNode):
                fields.append(self.add_field(c))
        regjson['fields'] = fields

        return regjson


    def add_field(self, field : FieldNode):
        fieldjson = {}

        swaccess = field.get_property("sw")
        onwrite = field.get_property("onwrite")
        onread = field.get_property("onread")
        hwaccess = field.get_property("hw")

        fieldjson['name'] = field.inst_name
        fieldjson['desc'] = field.get_property("desc", default="")
        fieldjson['bits'] = f"{field.high}:{field.low}"
        fieldjson['swaccess'] = access_from_sw(swaccess, onwrite, onread)
        fieldjson['hwaccess'] = access_from_hw(hwaccess)

        return fieldjson


    def generate_hjson(self, data, indent=2):
        lines = []
        for key, value in data.items():
            line = f"{key}: \"{value}\""
            lines.append(line)
        hjson_data = "\n".join(lines)
        return hjson_data
