import ctypes
import os
import random
import sys
import time
from ctypes import wintypes

WORK = r"C:\clfsfuzz"
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
CREATE_NEW = 1
OPEN_EXISTING = 3

clfs = ctypes.WinDLL("clfsw32.dll")
kernel32 = ctypes.WinDLL("kernel32.dll")

CreateLogFileW = clfs.CreateLogFile
CreateLogFileW.restype = wintypes.HANDLE
CreateLogFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]

AddLogContainerW = clfs.AddLogContainer
AddLogContainerW.restype = wintypes.BOOL
AddLogContainerW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR,
                             ctypes.c_void_p]

CloseHandle = kernel32.CloseHandle
CloseHandle.restype = wintypes.BOOL
CloseHandle.argtypes = [wintypes.HANDLE]


def make_seed():
    seed_path = os.path.join(WORK, "seed")
    cont_path = os.path.join(WORK, "seed0.blf")
    for p in (seed_path + ".blf", cont_path):
        if os.path.exists(p):
            os.remove(p)

    h = CreateLogFileW(seed_path, GENERIC_WRITE, FILE_SHARE_READ, None, CREATE_NEW, 0)
    if not h:
        raise RuntimeError("CreateLogFile failed: %d" % ctypes.get_last_error())

    if not AddLogContainerW(h, 0x100000, cont_path, None):
        raise RuntimeError("AddLogContainer failed: %d" % ctypes.get_last_error())

    CloseHandle(h)

    with open(seed_path + ".blf", "rb") as f:
        return f.read()


def mutate(seed, rng):
    data = bytearray(seed)
    n = rng.randint(1, 24)
    for _ in range(n):
        i = rng.randrange(len(data))
        mode = rng.randint(0, 3)
        if mode == 0:
            data[i] = rng.randrange(256)
        elif mode == 1:
            data[i] ^= 1 << rng.randrange(8)
        elif mode == 2:
            data[i] = 0xFF
        else:
            data[i] = 0x00
    return bytes(data)


def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    os.makedirs(WORK, exist_ok=True)

    seed = make_seed()
    print("seed size:", len(seed))

    rng = random.Random(0xC1F5)
    target = os.path.join(WORK, "case.blf")
    end = time.time() + seconds
    it = 0
    opened = 0

    while time.time() < end:
        payload = mutate(seed, rng)
        with open(target, "wb") as f:
            f.write(payload)

        h = CreateLogFileW(target, GENERIC_READ | GENERIC_WRITE,
                           FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0)
        if h:
            opened += 1
            CloseHandle(h)

        it += 1
        if it % 200 == 0:
            print("iter %d  opened %d  rng_state %d" % (it, opened, rng.getstate()[1][0]))
            sys.stdout.flush()

    print("done iters=%d opened=%d" % (it, opened))


if __name__ == "__main__":
    main()