import ctypes
import os
import subprocess
import sys

from ctypes import wintypes

WORK = r"C:\drvtest"
SC_MANAGER_CREATE_SERVICE = 0x0002
SERVICE_WIN32_OWN_PROCESS = 0x00000010
SERVICE_KERNEL_DRIVER = 0x00000001
SERVICE_DEMAND_START = 0x00000003
SERVICE_ERROR_NORMAL = 0x00000001
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020
SERVICE_CONTROL_STOP = 0x00000001

advapi = ctypes.WinDLL("advapi32.dll")

OpenSCManagerW = advapi.OpenSCManagerW
OpenSCManagerW.restype = wintypes.HANDLE
OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]

CreateServiceW = advapi.CreateServiceW
CreateServiceW.restype = wintypes.HANDLE
CreateServiceW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPCWSTR,
                           wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                           wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                           ctypes.c_void_p, wintypes.LPCWSTR, wintypes.LPCWSTR,
                           wintypes.LPCWSTR]

StartServiceW = advapi.StartServiceW
StartServiceW.restype = wintypes.BOOL
StartServiceW.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p]

ControlService = advapi.ControlService
ControlService.restype = wintypes.BOOL
ControlService.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p]

DeleteService = advapi.DeleteService
DeleteService.restype = wintypes.BOOL
DeleteService.argtypes = [wintypes.HANDLE]

CloseHandle = ctypes.WinDLL("kernel32.dll").CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
    return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode


def main():
    os.makedirs(WORK, exist_ok=True)
    src = os.path.join(WORK, "mini.c")
    sys_path = os.path.join(WORK, "mini.sys")

    print("=" * 55)
    print("1. write driver source")
    body = open(os.path.join(os.path.dirname(__file__), "mini.c"), "rb").read()
    with open(src, "wb") as f:
        f.write(body)
    print("   bytes:", len(body))

    print("=" * 55)
    print("2. locate vcvars")
    vs_root = r"C:\Program Files\Microsoft Visual Studio"
    found = None
    candidates = []
    if os.path.isdir(vs_root):
        for d in os.listdir(vs_root):
            candidates.append(os.path.join(vs_root, d, "Enterprise"))
            candidates.append(os.path.join(vs_root, d, "Professional"))
            candidates.append(os.path.join(vs_root, d, "Community"))
            candidates.append(os.path.join(vs_root, d, "BuildTools"))
    for ed in ("Enterprise", "Professional", "Community", "BuildTools"):
        candidates.append(os.path.join(r"C:\Program Files\Microsoft Visual Studio\2019", ed))
    for base in candidates:
        p = os.path.join(base, r"VC\Auxiliary\Build\vcvars64.bat")
        if os.path.exists(p):
            found = p
            break
    print("   vcvars:", found or "NOT FOUND")
    if not found:
        return

    print("=" * 55)
    print("3. compile with cl")
    cmd = 'cmd /c "call "%s" >nul && cl /nologo /c /GS- /Gs- "%s" /Fo"%s\\mini.obj" && link /nologo /DRIVER /SUBSYSTEM:NATIVE /ENTRY:DriverEntry /FORCE:UNRESOLVED /OUT:"%s" "%s\\mini.obj""' % (
        found, src, WORK, sys_path, WORK)
    out, err, rc = run(cmd)
    print("   rc:", rc)
    print("   err:", err[:600] if err else "(none)")
    print("   sys exists:", os.path.exists(sys_path),
          os.path.getsize(sys_path) if os.path.exists(sys_path) else 0)

    if not os.path.exists(sys_path):
        print("   ABORT: compile failed")
        return

    print("=" * 55)
    print("3. signature status of built driver")
    out, err, rc = run('powershell -c "(Get-AuthenticodeSignature \'%s\').Status"' % sys_path)
    print("   status:", out or err)

    print("=" * 55)
    print("4. open SCM and create service")
    hscm = OpenSCManagerW(None, None, SC_MANAGER_CREATE_SERVICE)
    if not hscm:
        print("   OpenSCManager failed:", ctypes.get_last_error())
        return

    name = "MiniKld"
    hs = CreateServiceW(hscm, name, name, 0xF003F,
                        SERVICE_KERNEL_DRIVER, SERVICE_DEMAND_START,
                        SERVICE_ERROR_NORMAL, sys_path, None, None, None, None, None)
    err_no = ctypes.get_last_error()
    print("   CreateService:", "OK" if hs else "FAIL err=%d" % err_no)

    if not hs:
        CloseHandle(hscm)
        return

    print("=" * 55)
    print("5. start the driver")
    ok = StartServiceW(hs, 0, None)
    start_err = ctypes.get_last_error()
    print("   StartService:", "OK" if ok else "FAIL err=%d (0x%X)" % (start_err, start_err))

    print("=" * 55)
    print("6. driver state")
    out, err, rc = run('sc query %s' % name)
    print(out if out else err)

    print("=" * 55)
    print("7. cleanup")
    if ok:
        ControlService(hs, SERVICE_CONTROL_STOP, None)
    DeleteService(hs)
    CloseHandle(hs)
    CloseHandle(hscm)
    print("   done")


if __name__ == "__main__":
    main()