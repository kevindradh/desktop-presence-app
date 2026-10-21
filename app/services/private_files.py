"""Restrict private files using POSIX modes or a protected Windows DACL."""
import os
from pathlib import Path


def restrict_path(path, *, directory=False):
    path = Path(path)
    if path.is_symlink():
        raise OSError('Private path must not be a symbolic link')
    if os.name != 'nt':
        path.chmod(0o700 if directory else 0o600)
        return
    import ctypes as c
    from ctypes import wintypes as w
    api = c.WinDLL('advapi32', use_last_error=True)
    kernel = c.WinDLL('kernel32', use_last_error=True)
    api.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)]
    api.OpenProcessToken.restype = w.BOOL
    api.GetTokenInformation.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)]
    api.GetTokenInformation.restype = w.BOOL
    api.ConvertSidToStringSidW.argtypes = [c.c_void_p, c.POINTER(w.LPWSTR)]
    api.ConvertSidToStringSidW.restype = w.BOOL
    api.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [w.LPCWSTR, w.DWORD, c.POINTER(c.c_void_p), c.POINTER(w.DWORD)]
    api.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = w.BOOL
    api.SetFileSecurityW.argtypes = [w.LPCWSTR, w.DWORD, c.c_void_p]
    api.SetFileSecurityW.restype = w.BOOL
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.LocalFree.argtypes = [c.c_void_p]
    kernel.LocalFree.restype = c.c_void_p
    token, sid_text, descriptor = w.HANDLE(), w.LPWSTR(), c.c_void_p()

    def checked(ok):
        if not ok:
            raise c.WinError(c.get_last_error())

    try:
        checked(api.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, c.byref(token)))
        size = w.DWORD()
        api.GetTokenInformation(token, 1, None, 0, c.byref(size))  # TokenUser
        if not size.value:
            raise c.WinError(c.get_last_error())
        info = c.create_string_buffer(size.value)
        checked(api.GetTokenInformation(token, 1, info, size, c.byref(size)))
        sid = c.cast(info, c.POINTER(c.c_void_p))[0]
        checked(api.ConvertSidToStringSidW(sid, c.byref(sid_text)))
        inherit = 'OICI' if directory else ''
        # Replace the DACL completely; inherited or explicit broad grants do not survive.
        sddl = f'D:P(A;{inherit};FA;;;SY)(A;{inherit};FA;;;{sid_text.value})'
        checked(api.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, c.byref(descriptor), None))
        checked(api.SetFileSecurityW(str(path), 0x80000004, descriptor))
    finally:
        if descriptor.value:
            kernel.LocalFree(descriptor)
        if sid_text:
            kernel.LocalFree(c.cast(sid_text, c.c_void_p))
        if token.value:
            kernel.CloseHandle(token)
