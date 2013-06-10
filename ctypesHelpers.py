
import ctypes

import memory	# For DerefPointer()

# HACK !!!
# HACK !!!
gProcessId = None
# HACK !!!
# HACK !!!

def Repr(self):
#	print('REPR! %s' % type(self))

	if self is None:
		return '<None>'
	elif not hasattr(self, '_fields_'):
		return '<no "_fields_" attr>'

	res = []
	for field in self._fields_:

#		print 'field:',field

		fieldName = field[0]
		value = getattr(self, fieldName)

		if hasattr(value, 'contents'):		# Field is a pointer!
			contents = memory.DerefPointer(value, gProcessId)
			contentsRepr = repr(contents)
			if len(contentsRepr.splitlines()) > 1:
				res.append('%s = \n' % (fieldName))
				for l in contentsRepr.splitlines():
					res.append('\t%s\n' % l)
			else:
				res.append('%s = %s\n' % (fieldName, contents))
#			print(repr(getattr(self,field[0]).contents))

		else:
			res.append('%s = %r' % (fieldName, value))
#			print(repr(value))
			res.append('\n')
#	return self.__class__.__name__ + '(\n' + ','.join(res) + ')'
	return self.__class__.__name__ + '(\n' + ''.join(res) + ')'

class _Structure(ctypes.Structure):
	__repr__ = Repr
class _Union(ctypes.Union):
	__repr__ = Repr

