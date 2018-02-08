# THIS FILE HAS BEEN GENERATED AUTOMATICALLY BY capnpy
# do not edit by hand
# generated on 2018-02-07 21:35

from capnpy.list import List as _List
from capnpy.list import StructItemType as _StructItemType
from capnpy.list import TextItemType as _TextItemType
from capnpy.segment.builder import SegmentBuilder as _SegmentBuilder
from capnpy.struct_ import Struct as _Struct
from capnpy.type import Types as _Types
from capnpy.util import check_version as _check_version
from capnpy.util import extend_module_maybe as _extend_module_maybe
from capnpy.util import text_repr as _text_repr

__capnpy_version__ = '0.4.1'
_check_version(__capnpy_version__)


#### FORWARD DECLARATIONS ####

class DataPathway(_Struct): pass


DataPathway.__name__ = 'DataPathway'


#### DEFINITIONS ####

@DataPathway.__extend__
class DataPathway(_Struct):
    __static_data_size__ = 0
    __static_ptrs_size__ = 2

    @property
    def struct_name(self):
        # no union check
        return self._read_str_text(0)

    def get_struct_name(self):
        return self._read_str_text(0, default_=b"")

    def has_struct_name(self):
        ptr = self._read_fast_ptr(0)
        return ptr != 0

    @property
    def handlers(self):
        # no union check
        return self._read_list(8, _TextItemType(_Types.text))

    def get_handlers(self):
        res = self.handlers
        if res is None:
            return _List.from_buffer(b'', 0, 0, 0, _TextItemType(_Types.text))
        return res

    def has_handlers(self):
        ptr = self._read_fast_ptr(8)
        return ptr != 0

    @staticmethod
    def __new(struct_name=None, handlers=None):
        builder = _SegmentBuilder()
        pos = builder.allocate(16)
        builder.alloc_text(pos + 0, struct_name)
        builder.copy_from_list(pos + 8, _TextItemType(_Types.text), handlers)
        return builder.as_string()

    def __init__(self, struct_name=None, handlers=None):
        _buf = DataPathway.__new(struct_name, handlers)
        self._init_from_buffer(_buf, 0, 0, 2)

    def shortrepr(self):
        parts = []
        if self.has_struct_name(): parts.append("struct_name = %s" % _text_repr(self.get_struct_name()))
        if self.has_handlers(): parts.append("handlers = %s" % self.get_handlers().shortrepr())
        return "(%s)" % ", ".join(parts)


_DataPathway_list_item_type = _StructItemType(DataPathway)

_extend_module_maybe(globals(), modname=__name__)
