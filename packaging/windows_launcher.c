#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

/* Resolve all paths against the executable, never against the caller's cwd. */
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show) {
    wchar_t directory[32768], python[32768], command[32768];
    DWORD length = GetModuleFileNameW(NULL, directory, 32768);
    if (!length || length >= 32768) return 1;
    wchar_t *separator = wcsrchr(directory, L'\\');
    if (!separator) return 1;
    *separator = L'\0';
    if (swprintf(python, 32768, L"%ls\\app\\pythonw.exe", directory) < 0) return 1;
    if (swprintf(command, 32768, L"\"%ls\" \"%ls\\app\\main.py\" %ls", python, directory, args) < 0) return 1;
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, 0, NULL, directory, &startup, &process)) {
        MessageBoxW(NULL, L"Could not start PythonTech. Extract the complete ZIP before launching.", L"PythonTech", MB_OK | MB_ICONERROR);
        return 1;
    }
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return (int)code;
}
