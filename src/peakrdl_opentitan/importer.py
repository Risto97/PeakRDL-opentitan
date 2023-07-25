from typing import Optional, List, Dict, Any, Type, Union, Set
import re

import hjson

from systemrdl import RDLCompiler, RDLImporter, Addrmap
from systemrdl import rdltypes
from systemrdl.messages import SourceRefBase
from systemrdl import component as comp

from .typemaps import sw_from_access, hw_from_access


class OpenTitanImporter(RDLImporter):

    def __init__(self, compiler: RDLCompiler):
        """
        Parameters
        ----------
        compiler:
            Reference to ``RDLCompiler`` instance to bind the importer to.
        """

        super().__init__(compiler)

    @property
    def src_ref(self) -> SourceRefBase:
        return self.default_src_ref


    def import_file(self, path: str, remap_state: Optional[str] = None) -> None:
        """
        Import a single OpenTitan HWJson file into the SystemRDL namespace.

        Parameters
        ----------
        path:
            Input OpenTitan HWJson file.
        """
        super().import_file(path)

        # tree = ElementTree.parse(path)
        tree = None
        with open(path) as f:
            tree = hjson.load(f)

        self.regwidth = None
        self.__addroffset = 0

        self.import_ip(tree)

    unsupported_addrmap_props = ["cip_id",
                        "bus_interfaces",
                        "revisions",
                        "design_spec",
                        "dv_doc",
                        "hw_checklist",
                        "sw_checklist",
                        "design_stage",
                        "dif_stage",
                        "verification_stage",
                        "notes",
                        "version",
                        "life_stage",
                        "commit_id",
                        "alert_list",
                        "available_inout_list",
                        "available_input_list",
                        "available_output_list",
                        "expose_reg_if",
                        "interrupt_list",
                        "inter_signal_list",
                        "no_auto_id_regs",
                        "no_auto_feat_regs",
                        "no_auto_intr_regs",
                        "no_auto_alert_regs",
                        "param_list",
                        "reset_request_list",
                        "scan",
                        "scan_reset",
                        "scan_en",
                        "SPDX-License-Identifier",
                        "wakeup_list",
                        "countermeasure"
                        ]

    unsupported_reg_props = [
                        "alias_target",   #	optional	string	name of the register to apply the alias definition to.
                        "async",   #	optional	string	indicates the register must cross to a different clock domain before use. The value shown here should correspond to one of the module’s clocks.
                        "sync",   #	optional	string	indicates the register needs to be on another clock/reset domain.The value shown here should correspond to one of the module’s clocks.
                        "hwext",   #	optional	string	‘true’ if the register is stored outside of the register module
                        "hwqe",   #	optional	string	‘true’ if hardware uses ‘q’ enable signal, which is latched signal of software write pulse.
                        "hwre",   #	optional	string	‘true’ if hardware uses ‘re’ signal, which is latched signal of software read pulse.
                        "regwen",   #	optional	string	if register is write-protected by another register, that register name should be given here. empty-string for no register write protection
                        "tags",   #	optional	string	tags for the register, following the format ‘tag_name:item1:item2…’
                        "shadowed",   #	optional	string	‘true’ if the register is shadowed
                        "update_err_alert",   #	optional	string	alert that will be triggered if this shadowed register has update error
                        "storage_err_alert",   #	optional	string	alert that will be triggered if this shadowed register has storage error
                        ]

    unsupported_field_props = [
                        "alias_target",   #	optional	string	name of the field to apply the alias definition to.
                        "hwqe",   #	optional	bitrange	‘true’ if hardware uses ‘q’ enable signal, which is latched signal of software write pulse. Copied from register if not provided in field. (Tool adds if not provided.)
                        "tags",   #	optional	string	tags for the field, followed by the format ‘tag_name:item1:item2…’
                        "mubi",   #	optional	bitrange	boolean flag for whether the field is a multi-bit type
                        "auto_split",   #	optional	bitrange	boolean flag which determines whether the field should be automatically separated into 1-bit sub-fields.This flag is used as a hint for automatically generated software headers with register description.
                        ]

    def warn_unsupported(self, key: str, tree: Dict):
        if key in tree:
            self.msg.warning(f"Unsupported key: {key}", self.src_ref)
        
    def import_ip(self, tree: Dict ) -> None:
        for prop in OpenTitanImporter.unsupported_addrmap_props:
            self.warn_unsupported(prop, tree)

        # Check for required values
        name = tree['name']
        if not name:
            self.msg.fatal("memoryMap is missing required tag 'name'", self.src_ref)

        # Create named component definition
        C_def = self.create_addrmap_definition(name)

        if 'human_name' in tree:
            self.assign_property(C_def, "name", tree['name'])

        if 'one_paragraph_desc' in tree:
            self.assign_property(C_def, "desc", tree['one_paragraph_desc']) 
        elif 'one_line_desc' in tree:               # Use one_paragraph_desc if both set
            self.assign_property(C_def, "desc", tree['one_line_desc'])

        self.add_signals(C_def, tree)

        if 'regwidth' in tree:
            self.regwidth = int(tree['regwidth'])
        else:
            self.regwidth = 32 # Default for regtool is 32

        self.add_registers(C_def, tree)

        self.register_root_component(C_def)

    def create_signal_definition(self, type_name: Optional[str] = None, src_ref: Optional[SourceRefBase] = None) -> comp.Signal:
        """
        Parameters
        ----------
        type_name: str
        src_ref: :class:`~SourceRefBase`

        Returns
        -------
        :class:`~comp.Signal`
            Component definition
        """
        return self._create_definition(comp.Signal, type_name, src_ref)

    def add_signals(self, node : Addrmap, tree: Dict): # TODO FINISH

        for sig_type in ['input', 'output', 'inout']:
            list_type = f'available_{sig_type}_list'
            if list_type in tree:
                for s in tree[list_type]:
                    self.create_signal_definition(s['name'])


    def add_registers(self, node : Addrmap, tree: Dict): # TODO FINISH

        for reg in tree['registers']:
            R = self.create_register(reg)
            self.add_child(node, R)

        pass

    def create_register(self, reg_dict: Dict) -> comp.Reg:
        for prop in OpenTitanImporter.unsupported_reg_props:
            self.warn_unsupported(prop, reg_dict)

        R = self.instantiate_reg(
                comp_def=self.create_reg_definition(type_name=reg_dict['name']),
                inst_name=reg_dict['name'],
                addr_offset=self.__addroffset, # TODO
                )
        self.__addroffset += self.regwidth//8  # TODO, any other case???

        self.assign_property(R, 'desc', reg_dict['desc'])

        swaccess = reg_dict['swaccess']    if 'swaccess' in reg_dict else None
        hwaccess = reg_dict['hwaccess']    if 'hwaccess' in reg_dict else None
        resval   = self.hex_or_dec_to_dec(reg_dict['resval']) if 'resval'   in reg_dict else 0

        self.add_fields(R, reg_dict, swaccess, hwaccess, resval)

        return R

    def add_fields(self,
                   reg: comp.Reg,
                   reg_dict: Dict,
                   default_swaccess : "str|None" = None,
                   default_hwaccess : "str|None" = None,
                   reg_resval       : int        = 0,
                   ):

        for field in reg_dict['fields']:
            F = self.create_field(field, default_swaccess, default_hwaccess, reg_resval)
            self.add_child(reg, F)

    def create_field(self,
                   field_dict: Dict,
                   default_swaccess : "str|None" = None,
                   default_hwaccess : "str|None" = None,
                   reg_resval       : int        = 0,
                   ):
        for prop in OpenTitanImporter.unsupported_field_props:
            self.warn_unsupported(prop, field_dict)

        if 'name' in field_dict:
            name = field_dict['name']
        else:
            name =  "val"  # TODO default name

        bits = [int(part) for part in field_dict['bits'].split(':')]
        if len(bits) == 2:
            bit_offset = bits[1]
            bit_width = (bits[0] - bits[1]) + 1
        elif len(bits) == 1:
            bit_offset = bits[0]
            bit_width = 1
        else:
            assert False

        F = self.instantiate_field(
                comp_def=self.create_field_definition(name),
                inst_name=name,
                bit_offset=bit_offset,
                bit_width=bit_width,
                )

        val = self.assign_property(F, 'desc', field_dict['desc']) if 'desc' in field_dict else None

        swaccess = field_dict['swaccess'] if 'swaccess' in field_dict else default_swaccess
        hwaccess = field_dict['hwaccess'] if 'hwaccess' in field_dict else default_hwaccess

        sw, onwrite, onread = sw_from_access(swaccess)

        self.assign_property(F, "sw", sw)
        val = self.assign_property(F, "onwrite", onwrite) if onwrite is not None else None
        val = self.assign_property(F, "onread", onread) if onread is not None else None

        if 'resval' in field_dict:
            resval = field_dict['resval']
            if resval == 'x':
                self.msg.warning(f"Unsupported resval value: {resval}, using 0 instead")
                resval = 0
            resval = self.hex_or_dec_to_dec(resval)
        else:
            resval = (reg_resval & ((2**bit_width-1) << bit_offset)) >> bit_offset

            self.assign_property(F, "reset", resval)

        if 'enum' in field_dict:
            enum = self.parse_enum(field_dict)
            self.assign_property(F, "encode", enum)

        return F

    def parse_enum(self, field_dict: Dict) -> Type[rdltypes.UserEnum]:

        members = []
        for enum in field_dict['enum']:
            if enum['name'][0].isdigit():
                self.msg.warning(f"Enumeration name cannot start with number: {enum['name']}, prepending underscore: _{enum['name']}")
                enum['name'] = "_" + enum['name']

            members.append(rdltypes.UserEnumMemberContainer(
                    name=enum['name'],
                    value=int(enum['value']),
                    rdl_name=None,
                    rdl_desc=enum['desc'],
                    ))

        enum_type = rdltypes.UserEnum.define_new(field_dict['name'] + "_e", members)
        return enum_type

    def hex_or_dec_to_dec(self, num : "str|int"):
        if isinstance(num, str):
            if num.startswith("0x"):
                return int(num, 16)
            return int(num)
        else:
            return num
