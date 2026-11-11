import os
import subprocess
import sys

WORK = r"C:\smstest"


def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return (r.stdout or "").strip(), (r.stderr or "").strip(), r.returncode
    except Exception as e:
        return "", repr(e), -1


def main():
    os.makedirs(WORK, exist_ok=True)
    exe = os.path.join(WORK, "plain.exe")

    with open(exe, "wb") as f:
        f.write(b"MZ")

    print("=" * 50)
    print("1. build unsigned exe")
    out, err, rc = run('powershell -c "Copy-Item %s\\System32\\whoami.exe %s"' % (os.environ["SystemRoot"], exe))
    print("   size:", os.path.getsize(exe) if os.path.exists(exe) else "MISSING")

    print("=" * 50)
    print("2. signature status")
    out, err, rc = run('powershell -c "(Get-AuthenticodeSignature \'%s\').Status"' % exe)
    print("   Get-AuthenticodeSignature:", out or err)

    print("=" * 50)
    print("3. MOTW streams (before)")
    out, err, rc = run('powershell -c "Get-Item \'%s\' -Stream * | Select-Object -Expand Stream" 2>$null' % exe)
    print("   streams:", out if out else "(none)")

    print("=" * 50)
    print("4. add MOTW manually")
    zone = "Zone.Identifier"
    setter = os.path.join(WORK, "set_motw.ps1")
    with open(setter, "w") as f:
        f.write('[ZoneTransfer]\nZoneId=3\n')
    out, err, rc = run('powershell -c "Set-Content -Path \'%s\' -Stream Zone.Identifier -Value (Get-Content \'%s\')"' % (exe, setter))
    print("   set:", rc)

    out, err, rc = run('powershell -c "Get-Content \'%s\' -Stream Zone.Identifier"' % exe)
    print("   MOTW now:", out or err or "(none)")

    print("=" * 50)
    print("5. SmartScreen policy state")
    for path in [
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SmartScreenEnabled",
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System\EnableSmartScreen",
        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SmartScreenEnabled",
    ]:
        out, err, rc = run('reg query "%s"' % path)
        val = out.splitlines()[-1].strip() if out else "(absent)"
        print("   %-70s %s" % (path.split("\\")[-1] + "  [" + path[:40] + "]", val))

    print("=" * 50)
    print("6. SmartScreen processes")
    out, err, rc = run('tasklist /FI "IMAGENAME eq smartscreen.exe" /NH')
    print("   smartscreen.exe:", out or "(not running)")

    print("=" * 50)
    print("7. execute with MOTW present")
    out, err, rc = run('"%s" /user' % exe)
    print("   rc=%s out=%s" % (rc, out[:200]))

    print("=" * 50)
    print("8. remove MOTW, execute again")
    out, err, rc = run('powershell -c "Remove-Item -Path \'%s\' -Stream Zone.Identifier"' % exe)
    out, err, rc = run('powershell -c "Get-Item \'%s\' -Stream * | Select-Object -Expand Stream" 2>$null' % exe)
    print("   streams after:", out if out else "(none)")
    out, err, rc = run('"%s" /user' % exe)
    print("   rc=%s out=%s" % (rc, out[:200]))

    print("=" * 50)
    print("9. driver signature enforcement")
    out, err, rc = run('bcdedit /enum {current} | findstr /i "testsigning nointegritychecks"')
    print("   bcdedit:", out if out else "(no testsigning / default = enforced)")

    out, err, rc = run('powershell -c "Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\\Microsoft\\Windows\\DeviceGuard | Select-Object -Expand SecurityServicesRunning" 2>$null')
    print("   DeviceGuard services:", out if out else "(none)")


if __name__ == "__main__":
    main()