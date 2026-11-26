"""Cooperative PID-marker reservation groups, for isolated qualification.
Use only owner-controlled directories; not an adversarial filesystem boundary.
Never remove a pre-existing or changed marker. No process launch authority.
"""
import os,re,stat
from pathlib import Path
DEVICES={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
def _plain(st,kind):
    return kind(st.st_mode) and not stat.S_ISLNK(st.st_mode) and not (getattr(st,'st_file_attributes',0)&0x400)
def _identity(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
class Reservation:
    def __init__(self,root,names):
        root=Path(root)
        try:st=root.lstat()
        except OSError as e:raise ValueError('existing reservation directory required') from e
        if not _plain(st,stat.S_ISDIR):raise ValueError('unsafe directory')
        if not isinstance(names,(tuple,list)) or not 1<=len(names)<=32:raise ValueError('lock names')
        if any(not isinstance(n,str) or not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]{0,95}\.lock',n) or n.split('.')[0].upper() in DEVICES for n in names):raise ValueError('lock name')
        if len({n.casefold() for n in names})!=len(names):raise ValueError('duplicate lock name')
        self.root=root.resolve();self.names=sorted(names,key=str.casefold);self._owned=[];self._used=False
        self.payload=str(os.getpid()).encode('ascii')
    def __enter__(self):
        if self._used:raise ValueError('reservation is single-use')
        self._used=True
        try:
            for n in self.names:
                p=self.root/n
                fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_BINARY',0),0o600)
                try:
                    # On write/fsync failure leave this marker fail-closed; only
                    # fully recorded ownership enters the rollback set.
                    if os.write(fd,self.payload)!=len(self.payload):raise OSError('short marker write')
                    os.fsync(fd)
                    identity=_identity(os.fstat(fd))
                finally:os.close(fd)
                self._owned.append((p,identity))
            return self
        except BaseException:
            self._release()
            raise
    def _release(self):
        problems=[]
        for p,identity in reversed(self._owned):
            try:
                s=p.lstat()
                if not _plain(s,stat.S_ISREG) or _identity(s)!=identity:raise ValueError('marker identity changed')
                with p.open('rb') as f:
                    if _identity(os.fstat(f.fileno()))!=identity or f.read(128)!=self.payload:raise ValueError('marker content changed')
                if _identity(p.lstat())!=identity:raise ValueError('marker changed before release')
                p.unlink()
            except (OSError,ValueError) as e:problems.append(f'{p.name}: {e}')
        self._owned.clear()
        if problems:raise ValueError('reservation release refused: '+'; '.join(problems))
    def __exit__(self,typ,value,tb):
        self._release()
        return False
