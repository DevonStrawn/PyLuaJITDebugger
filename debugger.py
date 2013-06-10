
import ctypes, _ctypes
from ctypes import c_void_p, c_uint8, c_uint32, c_uint64, c_int32, c_double, POINTER
import win32api

# HACK
# HACK
import ctypesHelpers
# HACK
# HACK

import memory, LuaJIT

# TODO MAGIC NUMBERS !!!!!
processName = 'LuaShell.EXE'
luaStateAddr = 0x00748d68

# Monkey patch _ctypes._Pointer !!!!!!!!!


PROCESS_ALL_ACCESS = 0x1f0fff








import psutil

# Returns a list of process IDs
def FindProcessIDs(processName):

	processes = [ process for process in psutil.process_iter() if str.lower(process.name) == str.lower(processName) ]

#	for process in psutil.process_iter():
#		processList = psutil.get_process_list()
#		processes = [ process for process in processList if str.lower(process.name) == str.lower(processName) ]
	# TODO Prioritize processes running under the debugger ?
	return [ process.pid for process in processes ]

def FindFirstProcessID(processName):

	for process in psutil.process_iter():
		if str.lower(process.name) == str.lower(processName):
			return [ process.pid ]

def OpenDebuggeeProcess():
	print 'Retreiving list of running processes...'
#	processIDs = FindProcessIDs(processName)
	processIDs = FindFirstProcessID(processName)		# WORKAROUND Temporary optimization, because psutil uses EnumProcesses(), which is slow !!!

	if processIDs is None or len(processIDs) <= 0:
		print 'No processes running for executable: "%s"' % processName
		return None, None

	print 'Found %d "%s" processes' % (len(processIDs), processName)

	processID = processIDs[0]


	# HACK
	# HACK
	# HACK
	ctypesHelpers.gProcessId = processID
	# HACK
	# HACK
	# HACK



	print 'Opening process %d' % processID
	processHandle = win32api.OpenProcess(PROCESS_ALL_ACCESS, 0, processID)

	return processHandle, processID




def ReadLuaState(address, processID = None):
	return memory.ReadStructureFromOtherProcessMemory(address, LuaJIT.lua_State, processID)

def DoIt():

	# Find all the LuaShell.EXE instances, in particular, one with a debugger attached!
	processHandle, processID = OpenDebuggeeProcess()

	# TODO Locate Lua VMs running in the process.
	# TODO ...
	# TODO ...


#	ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory

	c_lua_State = ReadLuaState(luaStateAddr, processID)

#	print c_lua_State.base, ctypes.addressof(c_lua_State.base.contents)
#	print dir(c_lua_State.base)
	print c_lua_State
	print '\n\n\n'
	print 'Thread top:', ctypes.addressof(c_lua_State.top) - ctypes.addressof(c_lua_State.base)
#	print 'Stack size:', 
	#define gcref(r)	((GCobj *)(uintptr_t)(r).gcptr32)
#	(&gcref((L->base-1)->fr.func)->fn)
	print 'Current function:', 


	stackTrace = []

	stack = []
	level = 0
	prev_is_tail = False
	while True:
		i_ci = LuaJIT.lua_getstack(c_lua_State, level,       luaStateAddr, processID)
		stackFrame = dict(level=level,i_ci=i_ci)
		stackTrace.append(stackFrame)
		level = level + 1
		if i_ci < 0 or level > 100:		# TODO This logic comes from `ngx-sample-lua-bt`.  Is it correct?
			break

		#printf("%d: i_ci: %s\\n", level, lua_getinfo(L, i_ci))
		frame = LuaJIT.lua_getinfo(c_lua_State, i_ci,          processID)
		stackFrame['frame'] = frame
		if frame == '':
			stack = []
			break

		if frame == "[tail]":
			if prev_is_tail:
				continue
			prev_is_tail = True
		else:
			prev_is_tail = False
		stack.append(frame)

	if len(stack) > 0:
		# TODO ???
		pass

	print len(stack), stack

	for stackFrame in stackTrace:
#		print 'level: %d, i_ci: %r, frame: %r' % (stackFrame['level'], stackFrame['i_ci'], stackFrame['frame'])
		print 'level: %2d, i_ci: %9r (offset: %3r, size: %3r), frame: %r' % (stackFrame['level'], stackFrame['i_ci'], stackFrame['i_ci'] & 0xffff, stackFrame['i_ci'] >> 16, stackFrame.get('frame', '<n/a>'))

if __name__ == "__main__":
	DoIt()
