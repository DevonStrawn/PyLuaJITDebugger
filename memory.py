

import ctypes
import win32process, win32api, win32ui

import process

import pdb;


def ReadNULLTerminatedStringFromOtherProcessMemory(address, processID):

	offset = 0
	characterBuffer = ctypes.create_string_buffer(1)
	ReadMem(address + offset, 1, characterBuffer, processID)

#	character = chr(characterBuffer[0])
	character = characterBuffer[0]
	characters = [ character ]
	while ord(character) != 0:
		ReadMem(address + offset, 1, characterBuffer, processID)
		character = characterBuffer[0]
		characters.append(character)
		offset = offset + 1

#	pdb.set_trace()

	return ''.join(characters)

def ReadStructureFromOtherProcessMemory(address, structureType, processID):
	# Buffer to store the read bytes.
	outBufferAddr = ctypes.create_string_buffer(ctypes.sizeof(structureType))
#	bytesRead = ctypes.c_size_t()
	c_structure = structureType()	# Allocate a structure in the *current* (!) process to mirror the structure from the *other* process.
	ReadMem(address, ctypes.sizeof(structureType), ctypes.byref(c_structure), processID)
	return c_structure

# TODO !!!
# TODO !!!
# TODO Don't open the process locally here !!!
# TODO !!!
# TODO !!!

def ReadMem(address, length, outputBufferAddr, processID):
	processHandle = process.GetProcessHandle(processID)

	# Buffer to store the read bytes.
	if outputBufferAddr == None:
		outputBufferAddr = ctypes.create_string_buffer(length)

	numBytesRead = ctypes.c_size_t()
#	result = ctypes.windll.kernel32.ReadProcessMemory(processHandle.handle, address, outputBufferAddr, length, ctypes.byref(numBytesRead))
	result = ctypes.windll.kernel32.ReadProcessMemory(processHandle.handle, address, outputBufferAddr, length, ctypes.byref(numBytesRead))
	if result == 0:
		lastError = ctypes.get_last_error()
		raise Exception('ReadProcessMemory() returned error (%r): %r' % (result, lastError))

	return outputBufferAddr

def DerefPointer(pointer, processID):
#	print 'POINTER!!!!! %s, pointer points to address (/has value): %s (%s)' % (type(pointer.contents), ctypes.addressof(pointer.contents), hex(ctypes.addressof(pointer.contents)))
#	res = []
#	res.append('%s = %r' % (fieldName, pointer))
#	res.append('\n')

	try:
#		ctypes.addressof(value.contents)
		if ctypes.addressof(pointer.contents) != 0:
#		if bool(pointer.contents):
	#		contents = pointer.contents
			pointedAtType = type(pointer.contents)
			typeInstanceInLocalMem = pointedAtType()
			contents = ReadMem(ctypes.addressof(pointer.contents), ctypes.sizeof(pointer.contents), None, processID)

			fit = min(len(contents), ctypes.sizeof(typeInstanceInLocalMem))

			# Copy 
			ctypes.memmove(ctypes.addressof(typeInstanceInLocalMem), contents, fit)

			return typeInstanceInLocalMem

			return contents
		else:
			return None
	except:
		pass
	return None

