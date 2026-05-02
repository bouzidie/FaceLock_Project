#pragma once
#include <windows.h>
#include <credentialprovider.h>
#include <strsafe.h>
#include <initguid.h>

// CLSID unique
DEFINE_GUID(CLSID_FaceLockCredentialProvider,
    0xA1B2C3D4, 0xE5F6, 0x7890, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0);

static const CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR s_rgCredProvFieldDescriptors[] = {
    { 0, CPFT_TILE_IMAGE, L"Image", CPFG_NONE },
    { 1, CPFT_LARGE_TEXT, L"FaceLock", CPFG_NONE },
    { 2, CPFT_SMALL_TEXT, L"En attente...", CPFG_NONE }
};

static const DWORD s_rgFieldStatePairs[] = {
    CPFS_DISPLAY_IN_BOTH, CPFIS_NONE,
    CPFS_DISPLAY_IN_BOTH, CPFIS_NONE,
    CPFS_DISPLAY_IN_SELECTED_TILE, CPFIS_NONE
};

class FaceLockCredentialProvider : public ICredentialProvider {
public:
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    STDMETHODIMP_(ULONG) AddRef() override;
    STDMETHODIMP_(ULONG) Release() override;

    STDMETHODIMP SetUsageScenario(CREDENTIAL_PROVIDER_USAGE_SCENARIO cpus, DWORD dwFlags) override;
    STDMETHODIMP SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs) override;
    STDMETHODIMP Advise(ICredentialProviderEvents* pcpe, uintptr_t upAdviseContext) override;
    STDMETHODIMP UnAdvise() override;
    STDMETHODIMP GetFieldDescriptorCount(DWORD* pdwCount) override;
    STDMETHODIMP GetFieldDescriptorAt(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) override;
    STDMETHODIMP GetCredentialCount(DWORD* pdwCount, DWORD* pdwDefault, BOOL* pbAutoLogonWithDefault) override;
    STDMETHODIMP GetCredentialAt(DWORD dwIndex, ICredentialProviderCredential** ppcpc) override;

    static HRESULT CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppv);

private:
    LONG _cRef;
    ICredentialProviderEvents* _pcpe;
    uintptr_t _upAdviseContext;
    CREDENTIAL_PROVIDER_USAGE_SCENARIO _cpus;
};

class FaceLockCredential : public ICredentialProviderCredential, public ICredentialProviderCredential2 {
public:
    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    STDMETHODIMP_(ULONG) AddRef() override;
    STDMETHODIMP_(ULONG) Release() override;

    // ICredentialProviderCredential (TOUTES LES MÉTHODES REQUISES)
    STDMETHODIMP Advise(ICredentialProviderCredentialEvents* pcpce) override;
    STDMETHODIMP UnAdvise() override;
    STDMETHODIMP SetSelected(BOOL* pbAutoLogon) override;
    STDMETHODIMP SetDeselected() override;
    STDMETHODIMP GetStringValue(DWORD dwFieldIndex, PWSTR* ppwsz) override;
    STDMETHODIMP GetBitmapValue(DWORD dwFieldIndex, HBITMAP* phbmp) override;
    STDMETHODIMP GetCheckboxValue(DWORD dwFieldIndex, int* pbChecked, PWSTR* ppwszLabel) override;
    STDMETHODIMP GetComboBoxValueCount(DWORD dwFieldIndex, DWORD* pcItems, DWORD* pdwDefaultItem) override;
    STDMETHODIMP GetComboBoxValueAt(DWORD dwFieldIndex, DWORD dwItem, PWSTR* ppwszItem) override;
    STDMETHODIMP GetSubmitButtonValue(DWORD dwFieldIndex, DWORD* pdwAdjacentTo) override;
    STDMETHODIMP SetStringValue(DWORD dwFieldIndex, LPCWSTR pwz) override;             // ✅ AJOUTÉ
    STDMETHODIMP SetCheckboxValue(DWORD dwFieldIndex, BOOL bChecked) override;          // ✅ AJOUTÉ
    STDMETHODIMP SetComboBoxSelectedValue(DWORD dwFieldIndex, DWORD dwSelectedItem) override; // ✅ AJOUTÉ
    STDMETHODIMP CommandLinkClicked(DWORD dwFieldIndex) override;                       // ✅ AJOUTÉ
    STDMETHODIMP SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs) override;
    STDMETHODIMP QueryContinue(IQueryContinueWithStatus* pqcws) override;
    STDMETHODIMP GetFieldState(DWORD dwFieldIndex, CREDENTIAL_PROVIDER_FIELD_STATE* pcpfs, CREDENTIAL_PROVIDER_FIELD_INTERACTIVE_STATE* pcpfis) override;
    STDMETHODIMP Submit(IQueryContinue* pqc) override;
    STDMETHODIMP GetFieldDescriptorCount(DWORD* pdwCount) override;
    STDMETHODIMP GetFieldDescriptorAt(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) override;
    STDMETHODIMP GetSerialization(CREDENTIAL_PROVIDER_GET_SERIALIZATION_RESPONSE* ppcgsr,
        CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs,
        PWSTR* ppwszOptionalStatusText,
        CREDENTIAL_PROVIDER_STATUS_ICON* pcsiOptionalStatusIcon) override;
    STDMETHODIMP ReportResult(NTSTATUS ntsStatus, NTSTATUS ntsSubstatus,
        PWSTR* ppwszOptionalStatusText,
        CREDENTIAL_PROVIDER_STATUS_ICON* pcsiOptionalStatusIcon) override;

    // ICredentialProviderCredential2
    STDMETHODIMP GetUserSid(PWSTR* ppwszSid) override;

    static HRESULT CreateInstance(IUnknown* pUnkOuter, REFIID riid, void** ppv);

private:
    LONG _cRef;
    ICredentialProviderCredentialEvents* _pcpce;
    HRESULT AuthenticateViaNamedPipe();
    void UpdateStatus(LPCWSTR status);
};