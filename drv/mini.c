typedef unsigned long ULONG;
typedef long long LONG_PTR;
typedef unsigned long long ULONG_PTR;
typedef void *PVOID;

typedef struct _UNICODE_STRING
{
    unsigned short Length;
    unsigned short MaximumLength;
    unsigned short *Buffer;
} UNICODE_STRING, *PUNICODE_STRING;

typedef struct _DRIVER_OBJECT
{
    short Type;
    short Size;
    void *DeviceObject;
    unsigned long Flags;
    void *DriverStart;
    unsigned long DriverSize;
    void *DriverSection;
    void *DriverExtension;
    struct
    {
        PUNICODE_STRING RegistryPath;
    } *DriverExtensionData;
    struct
    {
        PUNICODE_STRING DriverName;
    } *DriverNameData;
} DRIVER_OBJECT, *PDRIVER_OBJECT;

typedef struct _KLD_BASE
{
    unsigned int Magic;
    int Loaded;
    unsigned long long Tick;
} KLD_BASE, *PKLD_BASE;

static KLD_BASE g_State = {0x4B4C4431u, 1, 0};

static int KldEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
    (void)DriverObject;
    (void)RegistryPath;
    g_State.Tick = 0x12345678;
    return 0;
}

static void KldUnload(PDRIVER_OBJECT DriverObject)
{
    (void)DriverObject;
    g_State.Loaded = 0;
}

__declspec(dllexport) int KldGetState(void)
{
    return g_State.Loaded;
}

static void KldCreateSystemThreadCompat(void)
{
}

int __stdcall DriverEntry(void *DriverObject, void *RegistryPath)
{
    PDRIVER_OBJECT drv = (PDRIVER_OBJECT)DriverObject;

    drv->DriverSection = 0;
    (void)RegistryPath;
    (void)KldCreateSystemThreadCompat;

    return KldEntry(drv, (PUNICODE_STRING)RegistryPath);
}