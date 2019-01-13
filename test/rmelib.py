#from ctypes import cdll, wstring_at, create_unicode_buffer
import ctypes
#lib = cdll.WinDll('E:/Development/projects/C++/rmelib/Release/rme.dll')
lib = ctypes.cdll.LoadLibrary('E:/Development/projects/C++/rmelib/Release/rme.dll')
#lib = ctypes.cdll.LoadLibrary('E:/Development/projects/C++/rmelib/Release/Dll1.dll')
#lib = ctypes.cdll.LoadLibrary('E:\\Development\\projects\\C++\\rmelib\\Release\\.dll')

import platform
print (platform.architecture())

class CRMeAnnotation(object):
    def __init__(self, a):
        self.obj = a

    def get(self,i):
        #buf = create_unicode_buffer(257)
        lib.CRMeAnnotation_get.restype = ctypes.c_wchar_p
        ret = lib.CRMeAnnotation_get(self.obj, i)
        return ret

    @property
    def prompt(self):
        return self.get(5)
    @property
    def answer(self):
        return self.get(6)
    @property
    def situation(self):
        return self.get(7)
    @property
    def comment(self):
        return self.get(9)

    def toString(self):
        s = "s={s}, p={p}; a={a}, c={c}".format(s=self.situation.encode("utf8"), p=self.prompt.encode("utf8"), a=self.answer.encode("utf8"), c=self.comment.encode("utf8"))
        #prompt = self.prompt.encode("utf8")
        #answer = self.answer.encode("utf8")
        #s = "p={p}; a={a}".format(p=prompt, a= answer)
        return s


class CRMeAnnotationList(object):
    def __init__(self):
        #
        lib.CRMeAnnotationList_new.argtypes = None
        lib.CRMeAnnotationList_new.restype = ctypes.c_void_p
        lib.CRMeAnnotationList_destroy.argtypes = ctypes.c_void_p,
        lib.CRMeAnnotationList_destroy.restype = None
        self.obj = lib.CRMeAnnotationList_new()

    def __del__(self):
        #not sure about this^: gives Process finished with exit code -1073741819 (0xC0000005)
        if self.obj:
            print("destroying object    ")
            lib.CRMeAnnotationList_destroy(self.obj)

    def multiply(self, a, b):
        ret = lib.CRMeAnnotationList_multiply(self.obj,a, b)
        return ret

    def ReadFile(self, f):
        ret = lib.CRMeAnnotationList_ReadFile(self.obj, f)
        return ret

    def GetSize(self):
        ret = lib.CRMeAnnotationList_GetSize(self.obj)
        return ret

    def getFileName(self):
        #buf = create_unicode_buffer(257)
        lib.CRMeAnnotationList_getFileName.restype = ctypes.c_wchar_p
        #my_c_function.argtypes = [ctypes.c_char_p, ctypes_char_p]
        #lib.CRMeAnnotationList_getFileName.restype = ctypes.POINTER(ctypes.c_wchar)
        #lib.CRMeAnnotationList_getFileName2.restype = ctypes.POINTER(ctypes.wstring_at)
        ret = lib.CRMeAnnotationList_getFileName(self.obj)
        return ret

    def GetItem(self, i):
        return CRMeAnnotation(lib.CRMeAnnotationList_GetItem(self.obj, i))




#===============================================================================
# controlling functions
#===============================================================================
def start_f1(switch = False):

    print ("hello")
    lst = CRMeAnnotationList()
    f = ur"E:\RememberMe\test\Deutsch Englisch.rmedat"
    #print (a.multiply(2,4))
    ret = lst.ReadFile(f)
    if ret:
        n = lst.GetSize()
        print (lst.GetSize())
        #ctypes.wstring_at =
        print (lst.getFileName())

        for i in range(n):
            lstItem = lst.GetItem(i)
            #print (lstItem.get(5))
            print (lstItem.toString())



if __name__ == "__main__":
    start_f1(True)
    #update_from_repository()
