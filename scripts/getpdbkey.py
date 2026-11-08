import sys
import uuid
import pefile

pe = pefile.PE(sys.argv[1], fast_load=True)
pe.parse_data_directories(
    directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"]]
)
for entry in pe.DIRECTORY_ENTRY_DEBUG:
    data = pe.get_data(entry.struct.AddressOfRawData, entry.struct.SizeOfData)
    if data[:4] == b"RSDS":
        age = int.from_bytes(data[20:24], "little")
        candidates = [
            uuid.UUID(bytes_le=data[4:20]).hex.upper(),
            uuid.UUID(bytes=data[4:20]).hex.upper(),
            data[4:20].hex().upper(),
        ]
        seen = []
        for c in candidates:
            if c in seen:
                continue
            seen.append(c)
            print(f"{c}{age:x}")
        break
