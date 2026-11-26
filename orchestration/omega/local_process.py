"""Read-only local process identity/settlement observations.
A settled PID is not proof that descendant jobs or external locks are settled.
Caller must preserve a trusted launch identity; this module grants no authority.
"""
import os,socket,sys
from pathlib import Path

def _host():
    return socket.gethostname()

def _windows(pid):
    import ctypes
    from ctypes import wintypes
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
    k.OpenProcess.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=(wintypes.HANDLE,)
    k.CloseHandle.restype=wintypes.BOOL
    k.GetProcessTimes.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME),ctypes.POINTER(wintypes.FILETIME))
    k.GetProcessTimes.restype=wintypes.BOOL
    k.WaitForSingleObject.argtypes=(wintypes.HANDLE,wintypes.DWORD)
    k.WaitForSingleObject.restype=wintypes.DWORD
    h=k.OpenProcess(0x1000|0x100000,False,pid)
    if not h:
        return ('absent',None) if ctypes.get_last_error()==87 else ('unknown',None)
    try:
        birth,exit_time,kernel,user=(wintypes.FILETIME() for _ in range(4))
        if not k.GetProcessTimes(h,ctypes.byref(birth),ctypes.byref(exit_time),ctypes.byref(kernel),ctypes.byref(user)):return 'unknown',None
        identity=str((birth.dwHighDateTime<<32)|birth.dwLowDateTime)
        status=k.WaitForSingleObject(h,0)
        return ('settled' if status==0 else 'running' if status==258 else 'unknown'),identity
    finally:
        k.CloseHandle(h)

def _linux(pid):
    try:
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        stat=Path('/proc',str(pid),'stat').read_text()
        fields=stat[stat.rindex(')')+2:].split()
        if len(fields)<20 or not boot:return 'unknown',None
        return ('settled' if fields[0] in ('Z','X','x') else 'running'),boot+':'+fields[19]
    except FileNotFoundError:
        if Path('/proc/sys/kernel/random/boot_id').is_file() and not Path('/proc',str(pid)).exists():return 'absent',None
        return 'unknown',None
    except (OSError,ValueError,IndexError):return 'unknown',None

def _observe(pid):
    if type(pid) is not int or not 1<=pid<=0xffffffff:raise ValueError('invalid pid')
    if sys.platform=='win32':return _windows(pid)
    if sys.platform.startswith('linux'):return _linux(pid)
    return 'unknown',None

def capture(pid):
    state,birth=_observe(pid)
    if state!='running' or not birth:raise ValueError('live process identity unavailable')
    return {'pid':pid,'birth':birth,'platform':sys.platform,'host':_host()}

def settlement(identity):
    if not isinstance(identity,dict) or type(identity.get('pid')) is not int or not 1<=identity['pid']<=0xffffffff or not isinstance(identity.get('birth'),str) or not identity['birth'] or not isinstance(identity.get('platform'),str):raise ValueError('invalid process identity')
    if identity['platform']!=sys.platform or identity.get('host')!=_host():return {'state':'unknown','reason':'platform or host mismatch'}
    state,birth=_observe(identity['pid'])
    if state=='absent':return {'state':'settled','reason':'captured PID absent on this host'}
    if birth!=identity['birth']:return {'state':'unknown','reason':'process birth mismatch or unobservable'}
    return {'state':state,'reason':'matching process identity'}
