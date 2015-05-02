from rpython.rtyper.lltypesystem import rffi
from pypy.interpreter.error import oefmt
from pypy.interpreter.baseobjspace import W_Root
from pypy.module._cffi_backend.ctypeobj import W_CType
from pypy.module._cffi_backend import cffi_opcode, newtype


def getop(op):
    return rffi.cast(rffi.SIGNED, op) & 0xFF

def getarg(op):
    return rffi.cast(rffi.SIGNED, op) >> 8



class RealizeCache:
    NAMES = [None,
        "_Bool",
        "char",
        "signed char",
        "unsigned char",
        "short",
        "unsigned short",
        "int",
        "unsigned int",
        "long",
        "unsigned long",
        "long long",
        "unsigned long long",
        "float",
        "double",
        "long double",
        "wchar_t",
        "int8_t",
        "uint8_t",
        "int16_t",
        "uint16_t",
        "int32_t",
        "uint32_t",
        "int64_t",
        "uint64_t",
        "intptr_t",
        "uintptr_t",
        "ptrdiff_t",
        "size_t",
        "ssize_t",
        "int_least8_t",
        "uint_least8_t",
        "int_least16_t",
        "uint_least16_t",
        "int_least32_t",
        "uint_least32_t",
        "int_least64_t",
        "uint_least64_t",
        "int_fast8_t",
        "uint_fast8_t",
        "int_fast16_t",
        "uint_fast16_t",
        "int_fast32_t",
        "uint_fast32_t",
        "int_fast64_t",
        "uint_fast64_t",
        "intmax_t",
        "uintmax_t",
        ]
    def __init__(self, space):
        self.all_primitives = [None] * cffi_opcode._NUM_PRIM

def get_primitive_type(space, num):
    realize_cache = space.fromcache(RealizeCache)
    w_ctype = realize_cache.all_primitives[num]
    if w_ctype is None:
        if num == cffi_opcode.PRIM_VOID:
            w_ctype = newtype.new_void_type()
        elif 0 <= num < len(RealizeCache.NAMES) and RealizeCache.NAMES[num]:
            w_ctype = newtype.new_primitive_type(space, RealizeCache.NAMES[num])
        else:
            raise oefmt(ffi.space.w_NotImplementedError, "prim=%d", case)
        realize_cache.all_primitives[num] = w_ctype
    return w_ctype

def get_array_type(ffi, opcodes, itemindex, length):
    w_ctitem = realize_c_type(ffi, opcodes, itemindex)
    w_ctitemptr = newtype.new_pointer_type(ffi.space, w_ctitem)
    return newtype._new_array_type(ffi.space, w_ctitemptr, length)


class W_RawFuncType(W_Root):
    """Temporary: represents a C function type (not a function pointer)"""
    def __init__(self, w_ctfuncptr):
        self.w_ctfuncptr = w_ctfuncptr


def realize_c_type(ffi, opcodes, index):
    """Interpret an opcodes[] array.  If opcodes == ffi.ctxobj.ctx.c_types,
    store all the intermediate types back in the opcodes[].
    """
    x = _realize_c_type_or_func(ffi, opcodes, index)
    if isinstance(x, W_CType):
        return x
    else:
        xxxx


def _realize_c_type_or_func(ffi, opcodes, index):
    op = opcodes[index]

    from_ffi = False
    #...

    case = getop(op)

    if case == cffi_opcode.OP_PRIMITIVE:
        x = get_primitive_type(ffi.space, getarg(op))

    elif case == cffi_opcode.OP_POINTER:
        y = _realize_c_type_or_func(ffi, opcodes, getarg(op))
        if isinstance(y, W_CType):
            x = newtype.new_pointer_type(ffi.space, y)
        elif isinstance(y, W_RawFuncType):
            x = y.w_ctfuncptr
        else:
            raise NotImplementedError

    elif case == cffi_opcode.OP_ARRAY:
        x = get_array_type(ffi, opcodes, getarg(op),
                           rffi.cast(rffi.SIGNED, opcodes[index + 1]))

    elif case == cffi_opcode.OP_OPEN_ARRAY:
        x = get_array_type(ffi, opcodes, getarg(op), -1)

    elif case == cffi_opcode.OP_FUNCTION:
        y = realize_c_type(ffi, opcodes, getarg(op))
        base_index = index + 1
        num_args = 0
        OP_FUNCTION_END = cffi_opcode.OP_FUNCTION_END
        while getop(opcodes[base_index + num_args]) != OP_FUNCTION_END:
            num_args += 1
        ellipsis = (getarg(opcodes[base_index + num_args]) & 1) != 0
        fargs = [realize_c_type(ffi, opcodes, base_index + i)
                 for i in range(num_args)]
        w_ctfuncptr = newtype._new_function_type(ffi.space, fargs, y, ellipsis)
        x = W_RawFuncType(w_ctfuncptr)

    elif case == cffi_opcode.OP_NOOP:
        x = _realize_c_type_or_func(ffi, opcodes, getarg(op))

    else:
        raise oefmt(ffi.space.w_NotImplementedError, "op=%d", case)

    if from_ffi:
        yyyy # ...

    return x
