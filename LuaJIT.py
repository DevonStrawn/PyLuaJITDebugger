
import ctypes
from ctypes import c_void_p, c_uint8, c_uint32, c_uint64, c_int32, c_double, POINTER

import memory
from ctypesHelpers import _Structure, _Union

import os
import win32api, win32process


# ctypes adaptation of SystemTap's `user_uint32()` (http://sourceware.org/systemtap/tapsets/API-user-uint32.html)
def user_uint32(address, __processID):
	return memory.ReadStructureFromOtherProcessMemory(address, uint32_t, __processID)

# ctypes adaptation of SystemTap's `user_string()` (http://sourceware.org/systemtap/tapsets/API-user-string.html)
def user_string(address, __processID):
	return memory.ReadNULLTerminatedStringFromOtherProcessMemory(address, __processID)





uint8_t = ctypes.c_uint8
uint16_t = ctypes.c_uint16
uint32_t = ctypes.c_uint32
int32_t = ctypes.c_int32




'''
from ctypes import *
# from types import MethodType

def _rshift(self, other):
	if hasattr(other, 'value'):
		other = other.value
	return c_ulong(self.value >> other)

def _lshift(self, other):
	if hasattr(other, 'value'):
		other = other.value
	return c_ulong(self.value << other)

def _coerce(self, other):
	try:
		return self, self.__class__(other)
	except TypeError:
		return NotImplemented

# Add the functions to the type. A method is created when
# accessed as an attribute of an instance.
c_ulong.__lshift__ = _lshift
c_ulong.__rshift__ = _rshift
c_ulong.__coerce__ = _coerce
'''








MSize = c_uint32
lua_Number = c_double

#MRef = c_uint32			# TODO struct { uint32_t ptr32; };  	# Pseudo 32 bit pointer.
class MRef(_Structure):
	_fields_ = [ ('ptr32',   c_uint32) ]	# Pseudo 32 bit pointer.

#GCRef = c_uint32			# TODO struct { uint32_t ptr32; };  	# Pseudo 32 bit pointer.
class GCRef(_Structure):
	_fields_ = [ ('gcptr32',   c_uint32) ]	# Pseudo 32 bit pointer.

class FrameLink(_Union):
	_fields_ = [
		('ftsz',    c_int32),	# Frame type and size of previous frame.
		('pcr',     MRef),		# Overlaps PC for Lua frames.
	]

class TODO_ANONYMOUS(_Union):
	_fields_ = [
		('gcr',      GCRef),		# GCobj reference (if any).
		('i',        c_int32),		# Integer value.
	]

# TODO Use BigEndianStructure or LittleEndianStructure ???
class TODO_DUNNO(_Structure):
	_fields_ = [
		# TODO Endian-ness??? - these two members of this struct are wrapped in LJ_ENDIAN_LOHI(lo,hi) macro - which swaps their order on certain platforms!
		('TODO_ANONYMOUS',  TODO_ANONYMOUS),
		('it',              c_uint32),			# Internal object tag. Must overlap MSW of number.
	]

# TODO Use BigEndianStructure or LittleEndianStructure ???
class fr_STRUCT(_Structure):
	_fields_ = [
		# TODO Endian-ness??? - these two members of this struct are wrapped in LJ_ENDIAN_LOHI(lo,hi) macro - which swaps their order on certain platforms!
		('func',       GCRef),			# Function for next frame (or dummy L).
		('tp',	       FrameLink),		# Link to previous frame.
	]

# TODO Use BigEndianStructure or LittleEndianStructure ???
class u32_STRUCT(_Structure):
	_fields_ = [
		# TODO Endian-ness??? - these two members of this struct are wrapped in LJ_ENDIAN_LOHI(lo,hi) macro - which swaps their order on certain platforms!
		('lo',         c_uint32),			# Lower 32 bits of number.
		('hi',         c_uint32),			# Upper 32 bits of number.
	]

# Tagged value
# TODO this is declared "LJ_ALIGN(8)" in LuaJIT - replicate alignment here in ctypes ???
class TValue(_Union):
	_fields_ = [
		('u64',        c_uint64),			# 64 bit pattern overlaps number.
		('n',          lua_Number),			# Number object overlaps split tag/value object.
		('TODO_DUNNO', TODO_DUNNO),
		('fr',         fr_STRUCT),
		('u32',        u32_STRUCT),
	]

class lua_State(_Structure):
	_fields_ = [
		# "GCHeader"
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),

		('dummy_ffid', c_uint8),			# Fake FF_C for curr_funcisL() on dummy frames.
		('status',     c_uint8),			# Thread status.
		('glref',      MRef),				# Link to global state.
		('gclist',     GCRef),				# GC chain.
		('base',       POINTER(TValue)),	# Base of currently executing function.
		('top',        POINTER(TValue)),	# First free slot in the stack.
#		('base',       POINTER(c_uint64)),	# Base of currently executing function.
#		('top',        POINTER(c_uint64)),	# First free slot in the stack.

		('maxstack',   MRef),				# Last free slot in the stack.
		('stack',      MRef),				# Stack base.
		('openupval',  GCRef),				# List of open upvalues in the stack.
		('env',        GCRef),				# Thread environment (table of globals).
		('cframe',     c_void_p),			# End of C stack frame chain.
		('stacksize',  MSize),				# True stack size (incl. LJ_STACK_EXTRA).
	]




FRAME_LUA = 0
FRAME_VARG = 3
FRAME_TYPE = 3
FRAME_P    = 4
FRAME_TYPEP = (FRAME_TYPE | FRAME_P)

def tvref(mref): return mref.ptr32
def gcref(gcr): return gcr.gcptr32
def frame_gc(tvalue): return gcref(tvalue.fr.func)
def frame_ftsz(tvalue): return tvalue.fr.tp.ftsz
def frame_type(f): return frame_ftsz(f) & FRAME_TYPE
def frame_typep(f): return frame_ftsz(f) & FRAME_TYPEP
def frame_islua(f): return frame_type(f) == FRAME_LUA
def frame_pc(tvalue): return tvalue.fr.tp.pcr.ptr32

def bc_a(i):
	# dd(sprintf("instruction %d", i))
#	return (i >> 8) & 0xff
	return (i.value >> 8) & 0xff

#def frame_prevl(f):
def frame_prevl(f, fAddress,     __processID):
	pc = frame_pc(f)
	return fAddress - (1 + bc_a(user_uint32(pc - 4,    __processID))) * ctypes.sizeof(TValue)

def frame_isvarg(f): return frame_typep(f) == FRAME_VARG

def frame_sized(f):
	# /*
	#  * FRAME_TYPE == 3
	#  * FRAME_P    == 4
	#  * FRAME_TYPEP == (FRAME_TYPE | FRAME_P)
	#  */
	return frame_ftsz(f) & ~FRAME_TYPEP

def frame_prevd(f,   __frameAddress):
#def frame_prevd(f):
#	return f - frame_sized(f)
	return __frameAddress - frame_sized(f)

import sys

# code from function lj_debug_frame in LuaJIT 2.0
def lua_getstack(L, level, __addressOfL, __processID):

	# NOTE: `L` is a `lua_State` struct allocated in the current process, but its pointers point at addresses
	# NOTE: in the debuggee's memory space.  So *every* dereference requires that we allocate a local structure in
	# NOTE: the corresponding process to store the mirrored data.

#	print 'type(L): %r' % type(L)

	bot = tvref(L.stack) # `bot` : c_uint32, is a pointer to a `TValue`.  L.stack : MRef; tvref(mref) <=> mref.ptr32
	found_frame = False

#	print 'bot:', bot

#	for (nextframe = frame = L.base - ctypes.sizeof(TValue); frame > bot; ):

	addressOfNextFrameInDebuggeeMemory = ctypes.addressof(L.base.contents) - ctypes.sizeof(TValue)
	addressOfFrameInDebuggeeMemory = addressOfNextFrameInDebuggeeMemory

#	nextframe = ctypes.cast(ctypes.addressof(L.base.contents) - ctypes.sizeof(TValue), POINTER(TValue))
#	nextframe = ctypes.cast(ctypes.addressof(L.base.contents) - ctypes.sizeof(TValue), TValue)
	nextframe = memory.ReadStructureFromOtherProcessMemory(addressOfNextFrameInDebuggeeMemory, TValue, __processID)
	frame = nextframe

	while addressOfFrameInDebuggeeMemory > bot:
		#dd(sprintf("checking frame: %d, level: %d", frame, level))

		# Traverse frames backwards
		if frame_gc(frame) == __addressOfL:
			#dd("Skip dummy frames. See lj_meta_call")
			level = level + 1

		if level == 0:
			level = level - 1
			#dd(sprintf("Level found, frame=%p, nextframe=%p", frame, nextframe))
#			size = (nextframe - frame) / ctypes.sizeof(TValue)
			size = (addressOfNextFrameInDebuggeeMemory - addressOfFrameInDebuggeeMemory) / ctypes.sizeof(TValue)
			found_frame = True
			break
		level = level - 1

		nextframe, addressOfNextFrameInDebuggeeMemory = frame, addressOfFrameInDebuggeeMemory
		if frame_islua(frame):
#			addressOfFrameInDebuggeeMemory = frame_prevl(frame,     __processID)
			addressOfFrameInDebuggeeMemory = frame_prevl(frame, addressOfFrameInDebuggeeMemory,     __processID)
			frame = memory.ReadStructureFromOtherProcessMemory(addressOfFrameInDebuggeeMemory, TValue, __processID)
		else:
			if frame_isvarg(frame):
				#dd("Skip vararg pseudo-frame")
				level = level + 1
			addressOfFrameInDebuggeeMemory = frame_prevd(frame,     addressOfFrameInDebuggeeMemory)
			frame = memory.ReadStructureFromOtherProcessMemory(addressOfFrameInDebuggeeMemory, TValue, __processID)

	if not found_frame:
		#dd("Level not found")
		size = level
		frame = 0

	# code from function lua_getstatck in LuaJIT 2.0

#	if frame:
	if addressOfFrameInDebuggeeMemory != 0:
		i_ci = (size << 16) + (addressOfFrameInDebuggeeMemory - bot) / ctypes.sizeof(TValue)
		return i_ci

	return -1













# GC header for generic access to common fields of GC objects.
class GChead(_Structure):
	_fields_ = [
		# "GCHeader"
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),

		('unused1',    c_uint8),
		('unused2',    c_uint8),
		('env',        GCRef),
		('gclist',     GCRef),
		('metatable',  GCRef),
	]

# String object header. String payload follows.
class GCstr(_Structure):
	_fields_ = [
		# "GCHeader"
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),

		('reserved',   c_uint8),	# Used by lexer for fast lookup of reserved words.
		('unused',     c_uint8),
		('hash',       MSize),		# Hash of string.
		('len',        MSize),		# Size of string.
	]
'''
# If open: double linked list, anchored at thread.
class GCupval_anonymousUnion_anonymousStruct(_Structure):
	_fields_ = [
		('prev',         GCRef),
		('next',         GCRef),
	]

class GCupval_anonymousUnion(_Union):
	_fields_ = [
		('tv',         TValue),										# If closed: the value itself.
		('ANONYMOUS',  GCupval_anonymousUnion_anonymousStruct),		# If open: double linked list, anchored at thread.
	]

class GCupval(_Structure):
	_fields_ = [
		# "GCHeader"
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),

		('closed',     c_uint8),	# Set if closed (i.e. uv->v == &uv->u.value).
		('immutable',  c_uint8),	# Immutable value.

		('ANONYMOUS',  GCupval_anonymousUnion),

		('v',          MRef),		# Points to stack slot (open) or above (closed).
		('dhash',      c_uint32),	# Disambiguation hash: dh1 != dh2 => cannot alias.
	]
'''

BCLine = int32_t	# Bytecode line number.

class GCproto(_Structure):
	_fields_ = [
		# "GCHeader"
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),

		('numparams', uint8_t),		# Number of parameters.
		('framesize', uint8_t),		# Fixed frame size.
		('sizebc',    MSize),		# Number of bytecode instructions
		('gclist',    GCRef),		# 
		('k',         MRef),		# Split constant array (points to the middle).
		('uv',        MRef),		# Upvalue list. local slot|0x8000 or parent uv idx.
		('sizekgc',   MSize),		# Number of collectable constants.
		('sizekn',    MSize),		# Number of lua_Number constants.
		('sizept',    MSize),		# Total size including colocated arrays.
		('sizeuv',    uint8_t),		# Number of upvalues.
		('flags',     uint8_t),		# Miscellaneous flags (see below).
		('trace',     uint16_t),	# Anchor for chain of root traces.
	# ------ The following fields are for debugging/tracebacks only ------
		('chunkname', GCRef),		# Name of the chunk this function was defined in.
		('firstline', BCLine),		# First line of the function definition.
		('numline',   BCLine),		# Number of lines for the function definition.
		('lineinfo',  MRef),		# Compressed map from bytecode ins. to source line.
		('uvinfo',    MRef),		# Upvalue names.
		('varinfo',   MRef),		# Names and compressed extents of local variables.
	]

#typedef int (*lua_CFunction) (lua_State *L);
#lua_CFunction = ctypes.CFUNCTYPE(POINTER(lua_State))
lua_CFunction = c_uint32	# Pointer to a function!

class GCfuncC(_Structure):
	_fields_ = [
		# GCfuncHeader
		# -> GCHeader:
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),
		# -> rest of GCfuncHeader:
		('ffid',       uint8_t),
		('nupvalues',  uint8_t),
		('env',        GCRef),
		('gclist',     GCRef),
		('pc',         MRef),

		('f',          lua_CFunction),	# C function to be called.
		('upvalue',    TValue * 1),	# Array of upvalues (TValue).
	]

class GCfuncL(_Structure):
	_fields_ = [
		# GCfuncHeader
		# -> GCHeader:
		('nextgc',     GCRef),
		('marked',     c_uint8),
		('gct',        c_uint8),
		# -> rest of GCfuncHeader:
		('ffid',       uint8_t),
		('nupvalues',  uint8_t),
		('env',        GCRef),
		('gclist',     GCRef),
		('pc',         MRef),

		('uvptr',      GCRef * 1),	# Array of _pointers_ to upvalue objects (GCupval).
	]

class GCfunc(_Union):
	_fields_ = [
		('c', GCfuncC),
		('l', GCfuncL),
	]

class GCobj(_Union):
	_fields_ = [
		('gch',       GChead),
		('str',       GCstr),
#		('uv',        GCupval),
#		('th',        lua_State),
		('pt',        GCproto),
		('fn',        GCfunc),
#		('cd',        GCcdata),
#		('tab',       GCtab),
#		('ud',        GCudata),
	]



FF_LUA = 0

def frame_func(f,          __processID):
##	gcobj = frame_gc(f)
##	return gcobj.fn
##	gcobj = 
#	return frame_gc(f).fn

	gcobj = frame_gc(f)
	__GCObjInstance = memory.ReadStructureFromOtherProcessMemory(gcobj, GCobj, __processID)

	return __GCObjInstance.fn

def isluafunc(fn):
	# FF_LUA == 0
	return fn.c.ffid == FF_LUA

def funcproto(fn):
	return fn.l.pc.ptr32 - ctypes.sizeof(GCproto)

def strref(r, __processID):
	gcobj = gcref(r)
	__GCObjInstance = memory.ReadStructureFromOtherProcessMemory(gcobj, GCobj, __processID)
	return __GCObjInstance.str

def proto_chunkname(pt, __processID):
	return strref(pt.chunkname, __processID)

def strdata(s):
	return s + ctypes.sizeof(GCstr)







cfuncs = {}		# TODO Copied from Yuchin's example.

import winappdbg
import process

def lua_getinfo(L, i_ci, __processID):
	# code from function lj_debug_getinfo in LuaJIT 2.0

	offset = i_ci & 0xffff	# Offset = first 16 bits of `i_ci`
	if offset == 0:
		#dd(sprintf("assertion failed: offset == 0: i_ci=%x", i_ci))
		print "assertion failed: offset == 0: i_ci=%x" % i_ci
		return ''

	# LuaJIT frame stack is simply an array of TValue's.
	frame = tvref(L.stack) + offset * ctypes.sizeof(TValue)
	size = i_ci >> 16	# Size = first 16 bits of `i_ci`

	# TODO C code conditions on 'size' - is this correct???
	nextframe = None
	if size:
		nextframe = frame + size * ctypes.sizeof(TValue)
	else:
		nextframe = 0

	#dd(sprintf("getinfo: frame=%p nextframe=%p", frame, nextframe))

	# TODO C code conditions on 'size' - is this correct???
	maxstack = tvref(L.maxstack)
#	if (!(frame <= maxstack && (!nextframe || nextframe <= maxstack))) {
	if not (frame <= maxstack and ((not nextframe) or nextframe <= maxstack)):
		#dd("assertion failed: frame <= maxstack && (!nextframe || nextframe <= maxstack)")
		print "assertion failed: frame <= maxstack && (!nextframe || nextframe <= maxstack)"
		return ''

	__frameInstance = memory.ReadStructureFromOtherProcessMemory(frame, TValue, __processID)
#	print __frameInstance, frame
#	fn = frame_func(frame, __processID)
	fn = frame_func(__frameInstance,        __processID)

	# LJ_TFUNC == ~8u
	if not (fn.c.gct == 8):
		print "assertion failed: fn->c.gct == ~LJ_TFUNC: %d" % fn.c.gct
		#dd(sprintf("assertion failed: fn->c.gct == ~LJ_TFUNC: %d", $fn->c->gct))
		return ''

	if isluafunc(fn):
		pt = funcproto(fn)
		__ptInstance = memory.ReadStructureFromOtherProcessMemory(pt, GCproto, __processID)
		firstline = __ptInstance.firstline
		name = proto_chunkname(__ptInstance, __processID)  # GCstr *name


		# TODO srcdata() won't work as-is...
#		src = strdata(name)
		src = (gcref(__ptInstance.chunkname) + GCobj.str.offset) + ctypes.sizeof(GCstr)


		__stringBuffer = user_string(src, __processID)
#		return '%s:%d' % (__stringBuffer, firstline)
		return dict(filename=__stringBuffer, firstline=firstline)
#		return sprintf("%s:%d", user_string(src), firstline)


	# being a C function



	cfunc = fn.c.f
#	cFunctionAddressInDebuggeeProcess = ctypes.addressof(cfunc.contents)
	cFunctionAddressInDebuggeeProcess = cfunc

#	cFunctionName = dbghelp.symFromAddr(???)

	processHandle = process.GetProcessHandle(__processID)

	print 'processHandle', processHandle, processHandle.handle

	# TODO Handle exception, print GetLastError...(), etc.
	winappdbg.win32.SymSetOptions(winappdbg.win32.SYMOPT_UNDNAME | winappdbg.win32.SYMOPT_DEFERRED_LOADS)

#	os.path.dirname(win32api.GetModuleFilename(moduleHandle))
	executablePath = os.path.dirname(win32process.GetModuleFileNameEx(processHandle.handle, 0))

	# TODO Handle exception, print GetLastError...(), etc.
	winappdbg.win32.SymInitialize(processHandle.handle, UserSearchPath = executablePath, fInvadeProcess = False)




	# TODO Handle exception, print GetLastError...(), etc.
	try:
		c_symInfo = winappdbg.win32.SymFromAddr(processHandle.handle, cFunctionAddressInDebuggeeProcess)
		print c_symInfo, c_symInfo.Name
	except Exception, e:
		print e


	# TODO !!!
	return 'C FUNCTION - UNKNOWN NAME !!! @ %r' % fn.c.f

'''
	cfunc = fn.c.f
	sym = cfuncs[cfunc]
	if sym != '':
		return sym

	sym = "C:" . usymname(cfunc)
	cfuncs[cfunc] = sym

	return sym
'''
