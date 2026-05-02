#include "FaceLockCP.h"
#include <string>
#include <winerror.h>

// ========== ICredentialProvider ==========
HRESULT FaceLockCredentialProvider::QueryInterface(REFIID riid, void** ppv) {
    if (riid == IID_IUnknown || riid == IID_ICredentialProvider) {
        *ppv = static_cast<ICredentialProvider*>(this);
        AddRef(); return S_OK;
    }
    *ppv = nullptr; return E_NOINTERFACE;
}
ULONG FaceLockCredentialProvider::AddRef() { return InterlockedIncrement(&_cRef); }
ULONG FaceLockCredentialProvider::Release() {
    LONG cRef = InterlockedDecrement(&_cRef);
    if (cRef == 0) delete this;
    return cRef;
}
HRESULT FaceLockCredentialProvider::SetUsageScenario(CREDENTIAL_PROVIDER_USAGE_SCENARIO cpus, DWORD) {
    _cpus = cpus;
    return (cpus == CPUS_LOGON || cpus == CPUS_UNLOCK_WORKSTATION) ? S_OK : E_NOTIMPL;
}
HRESULT FaceLockCredentialProvider::SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION*) { return S_OK; }
HRESULT FaceLockCredentialProvider::Advise(ICredentialProviderEvents* pcpe, uintptr_t upAdviseContext) {
    _pcpe = pcpe; if (_pcpe) _pcpe->AddRef(); _upAdviseContext = upAdviseContext; return S_OK;
}
HRESULT FaceLockCredentialProvider::UnAdvise() {
    if (_pcpe) { _pcpe->Release(); _pcpe = nullptr; } return S_OK;
}
HRESULT FaceLockCredentialProvider::GetFieldDescriptorCount(DWORD* pdwCount) { *pdwCount = 3; return S_OK; }
HRESULT FaceLockCredentialProvider::GetFieldDescriptorAt(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) {
    if (dwIndex >= 3) return E_INVALIDARG;
    *ppcpfd = new CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR();
    (*ppcpfd)->dwFieldID = s_rgCredProvFieldDescriptors[dwIndex].dwFieldID;
    (*ppcpfd)->cpft = s_rgCredProvFieldDescriptors[dwIndex].cpft;
    (*ppcpfd)->pszLabel = s_rgCredProvFieldDescriptors[dwIndex].pszLabel;
    (*ppcpfd)->cpfg = s_rgCredProvFieldDescriptors[dwIndex].cpfg;
    return S_OK;
}
HRESULT FaceLockCredentialProvider::GetCredentialCount(DWORD* pdwCount, DWORD*, BOOL*) { *pdwCount = 1; return S_OK; }
HRESULT FaceLockCredentialProvider::GetCredentialAt(DWORD, ICredentialProviderCredential** ppcpc) {
    return FaceLockCredential::CreateInstance(nullptr, IID_ICredentialProviderCredential, (void**)ppcpc);
}
HRESULT FaceLockCredentialProvider::CreateInstance(IUnknown*, REFIID riid, void** ppv) {
    auto* p = new FaceLockCredentialProvider();
    if (!p) return E_OUTOFMEMORY;
    p->_cRef = 1; p->_pcpe = nullptr; p->_upAdviseContext = 0;
    HRESULT hr = p->QueryInterface(riid, ppv);
    p->Release(); return hr;
}

// ========== ICredentialProviderCredential ==========
HRESULT FaceLockCredential::QueryInterface(REFIID riid, void** ppv) {
    if (riid == IID_IUnknown || riid == IID_ICredentialProviderCredential) {
        *ppv = static_cast<ICredentialProviderCredential*>(this); AddRef(); return S_OK;
    }
    if (riid == IID_ICredentialProviderCredential2) {
        *ppv = static_cast<ICredentialProviderCredential2*>(this); AddRef(); return S_OK;
    }
    *ppv = nullptr; return E_NOINTERFACE;
}
ULONG FaceLockCredential::AddRef() { return InterlockedIncrement(&_cRef); }
ULONG FaceLockCredential::Release() {
    LONG cRef = InterlockedDecrement(&_cRef);
    if (cRef == 0) delete this; return cRef;
}

HRESULT FaceLockCredential::Advise(ICredentialProviderCredentialEvents* pcpce) { _pcpce = pcpce; if (_pcpce) _pcpce->AddRef(); return S_OK; }
HRESULT FaceLockCredential::UnAdvise() { if (_pcpce) { _pcpce->Release(); _pcpce = nullptr; } return S_OK; }
HRESULT FaceLockCredential::SetSelected(BOOL*) { return S_OK; }
HRESULT FaceLockCredential::SetDeselected() { return S_OK; }

HRESULT FaceLockCredential::GetStringValue(DWORD dwIndex, PWSTR* ppwsz) {
    const wchar_t* vals[] = { L"", L"FaceLock - Reconnaissance Faciale", L"En attente..." };
    if (dwIndex >= 3) return E_INVALIDARG;
    return SHStrDupW(vals[dwIndex], ppwsz);
}
HRESULT FaceLockCredential::GetBitmapValue(DWORD, HBITMAP*) { return E_NOTIMPL; }
HRESULT FaceLockCredential::GetCheckboxValue(DWORD, int*, PWSTR*) { return E_NOTIMPL; }
HRESULT FaceLockCredential::GetComboBoxValueCount(DWORD, DWORD*, DWORD*) { return E_NOTIMPL; }
HRESULT FaceLockCredential::GetComboBoxValueAt(DWORD, DWORD, PWSTR*) { return E_NOTIMPL; }
HRESULT FaceLockCredential::GetSubmitButtonValue(DWORD, DWORD*) { return E_NOTIMPL; }

// ✅ MÉTHODES AJOUTÉES (CORRECTION ERREUR C2259)
HRESULT FaceLockCredential::SetStringValue(DWORD, LPCWSTR) { return S_OK; }
HRESULT FaceLockCredential::SetCheckboxValue(DWORD, BOOL) { return E_NOTIMPL; }
HRESULT FaceLockCredential::SetComboBoxSelectedValue(DWORD, DWORD) { return E_NOTIMPL; }
HRESULT FaceLockCredential::CommandLinkClicked(DWORD) { return S_OK; }

HRESULT FaceLockCredential::SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION*) { return S_OK; }
HRESULT FaceLockCredential::QueryContinue(IQueryContinueWithStatus*) { return S_OK; }

HRESULT FaceLockCredential::GetFieldState(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_STATE* pcpfs, CREDENTIAL_PROVIDER_FIELD_INTERACTIVE_STATE* pcpfis) {
    if (dwIndex >= 3) return E_INVALIDARG;
    *pcpfs = (CREDENTIAL_PROVIDER_FIELD_STATE)s_rgFieldStatePairs[dwIndex * 2];
    *pcpfis = (CREDENTIAL_PROVIDER_FIELD_INTERACTIVE_STATE)s_rgFieldStatePairs[dwIndex * 2 + 1];
    return S_OK;
}
HRESULT FaceLockCredential::GetFieldDescriptorCount(DWORD* pdwCount) { *pdwCount = 3; return S_OK; }
HRESULT FaceLockCredential::GetFieldDescriptorAt(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) {
    if (dwIndex >= 3) return E_INVALIDARG;
    *ppcpfd = new CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR();
    (*ppcpfd)->dwFieldID = s_rgCredProvFieldDescriptors[dwIndex].dwFieldID;
    (*ppcpfd)->cpft = s_rgCredProvFieldDescriptors[dwIndex].cpft;
    (*ppcpfd)->pszLabel = s_rgCredProvFieldDescriptors[dwIndex].pszLabel;
    (*ppcpfd)->cpfg = s_rgCredProvFieldDescriptors[dwIndex].cpfg;
    return S_OK;
}

HRESULT FaceLockCredential::GetSerialization(CREDENTIAL_PROVIDER_GET_SERIALIZATION_RESPONSE* ppcgsr,
    CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs,
    PWSTR*, CREDENTIAL_PROVIDER_STATUS_ICON*) {
    *ppcgsr = CP_GSR_NO_CREDENTIAL;
    ZeroMemory(pcpcs, sizeof(*pcpcs));
    return S_OK;
}
HRESULT FaceLockCredential::ReportResult(NTSTATUS, NTSTATUS, PWSTR*, CREDENTIAL_PROVIDER_STATUS_ICON*) { return S_OK; }
HRESULT FaceLockCredential::GetUserSid(PWSTR* ppwszSid) { *ppwszSid = nullptr; return E_NOTIMPL; }

// ========== Métier ==========
void FaceLockCredential::UpdateStatus(LPCWSTR status) {
    if (_pcpce) _pcpce->SetFieldString(this, 2, status);
}
HRESULT FaceLockCredential::AuthenticateViaNamedPipe() {
    const wchar_t* pipeName = L"\\\\.\\pipe\\FaceLockPipe";
    HANDLE hPipe = CreateFileW(pipeName, GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING, 0, nullptr);
    if (hPipe == INVALID_HANDLE_VALUE) return HRESULT_FROM_WIN32(GetLastError());

    const char* req = "{\"image\":\"\",\"timestamp\":0}";
    DWORD written;
    WriteFile(hPipe, req, (DWORD)strlen(req), &written, nullptr);

    char resp[4096] = { 0 };
    DWORD read;
    ReadFile(hPipe, resp, sizeof(resp) - 1, &read, nullptr);
    CloseHandle(hPipe);

    std::string r(resp, read);
    return (r.find("\"status\":\"success\"") != std::string::npos) ? S_OK : E_FAIL;
}
HRESULT FaceLockCredential::Submit(IQueryContinue* pqc) {
    if (pqc) pqc->QueryContinue();
    HRESULT hr = AuthenticateViaNamedPipe();
    if (SUCCEEDED(hr)) {
        UpdateStatus(L"Authentifie...");
        if (_pcpce) _pcpce->OnCreatingWindow(nullptr);
        return S_OK;
    }
    UpdateStatus(L"Echec");
    return E_FAIL;
}
HRESULT FaceLockCredential::CreateInstance(IUnknown*, REFIID riid, void** ppv) {
    auto* p = new FaceLockCredential();
    if (!p) return E_OUTOFMEMORY;
    p->_cRef = 1; p->_pcpce = nullptr;
    HRESULT hr = p->QueryInterface(riid, ppv);
    p->Release(); return hr;
}