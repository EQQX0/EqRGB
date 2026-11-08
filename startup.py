"""Start EqRGB with Windows: the per-user Run entry the installer also writes (value "EqRGB")."""
import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE = "EqRGB"


def command(mode, here):
    """The Run value: pythonw (no console) + the app, with --tray to start hidden."""
    exe = sys.executable
    if os.path.basename(exe).lower() == "python.exe":
        exe = os.path.join(os.path.dirname(exe), "pythonw.exe")
    cmd = '"%s" "%s"' % (exe, os.path.join(here, "rgb_app.pyw"))
    return cmd + (" --tray" if mode != "window" else "")


def is_enabled():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, VALUE)
        return True
    except OSError:
        return False


def current_mode():
    """"tray" or "window" as the existing entry says, None when there is no entry."""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            return "tray" if "--tray" in winreg.QueryValueEx(k, VALUE)[0] else "window"
    except OSError:
        return None


def set_enabled(on, mode, here):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if on:
            winreg.SetValueEx(k, VALUE, 0, winreg.REG_SZ, command(mode, here))
        else:
            try:
                winreg.DeleteValue(k, VALUE)
            except FileNotFoundError:
                pass
