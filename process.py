
import win32api

PROCESS_ALL_ACCESS = 0x1f0fff
#global processID

processIDToProcessCache = {}

def GetProcessHandle(processID):
	processHandle = processIDToProcessCache.get(processID, None)
	if processHandle is None:
		processIDToProcessCache[processID] = processHandle = win32api.OpenProcess(PROCESS_ALL_ACCESS, 0, processID)		# TODO Don't hard-code! Cache 'process' instances in a look-up table !
	return processHandle


