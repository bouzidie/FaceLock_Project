#include <windows.h>
#include <credentialprovider.h>
#include <strsafe.h>
#include "FaceLockCP.h"

class ClassFactory : public IClassFactory {
public:
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) {
        if (riid == IID_IUnknown || riid == IID_IClassFactory) {
            *ppv = this;
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    STDMETHODIMP_(ULONG) AddRef() { return InterlockedIncrement(&_ref); }
    STDMETHODIMP_(ULONG) Release() {
        LONG r = InterlockedDecrement(&_ref);
        if (!r) delete this;
        return r;
    }
    STDMETHODIMP CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppv) {
        return FaceLockCredentialProvider::CreateInstance(pUnkOuter, riid, ppv);
    }
    STDMETHODIMP LockServer(BOOL) { return S_OK; }
private:
    LONG _ref = 0;
};

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void** ppv) {
    if (rclsid == CLSID_FaceLockCredentialProvider) {
        auto* f = new ClassFactory();
        if (!f) return E_OUTOFMEMORY;
        HRESULT hr = f->QueryInterface(riid, ppv);
        f->Release();
        return hr;
    }
    return CLASS_E_CLASSNOTAVAILABLE;
}

STDAPI DllRegisterServer() {
    HKEY hKey;
    const wchar_t* clsid = L"{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}";
    wchar_t path[MAX_PATH], dllPath[MAX_PATH];

    GetModuleFileNameW(nullptr, dllPath, MAX_PATH);
    StringCchPrintfW(path, MAX_PATH,
        L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Authentication\\Credential Providers\\%s",
        clsid);
    RegCreateKeyExW(HKEY_LOCAL_MACHINE, path, 0, nullptr, 0, KEY_WRITE, nullptr, &hKey, nullptr);
    RegSetValueExW(hKey, nullptr, 0, REG_SZ, (BYTE*)L"FACELOCK Credential Provider",
        wcslen(L"FACELOCK Credential Provider") * 2);
    RegCloseKey(hKey);

    StringCchPrintfW(path, MAX_PATH, L"CLSID\\%s\\InprocServer32", clsid);
    RegCreateKeyExW(HKEY_CLASSES_ROOT, path, 0, nullptr, 0, KEY_WRITE, nullptr, &hKey, nullptr);
    RegSetValueExW(hKey, nullptr, 0, REG_SZ, (BYTE*)dllPath, wcslen(dllPath) * 2);
    RegSetValueExW(hKey, L"ThreadingModel", 0, REG_SZ, (BYTE*)L"Apartment",
        wcslen(L"Apartment") * 2);
    RegCloseKey(hKey);
    return S_OK;
}

STDAPI DllUnregisterServer() {
    const wchar_t* clsid = L"{A1B2C3D4-E5F6-7890-1234-56789ABCDEF0}";
    wchar_t path[MAX_PATH];
    StringCchPrintfW(path, MAX_PATH,
        L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Authentication\\Credential Providers\\%s",
        clsid);
    SHDeleteKeyW(HKEY_LOCAL_MACHINE, path);
    StringCchPrintfW(path, MAX_PATH, L"CLSID\\%s", clsid);
    SHDeleteKeyW(HKEY_CLASSES_ROOT, path);
    return S_OK;
}

BOOL APIENTRY DllMain(HMODULE, DWORD, LPVOID) {
    return TRUE;
}