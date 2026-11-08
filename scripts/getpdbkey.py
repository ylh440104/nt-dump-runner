import sys
import pefile

pe = pefile.PE(sys.argv[1], fast_load=True)
pe.parse_data_directories(
    directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"]]
)
for entry in pe.DIRECTORY_ENTRY_DEBUG:
    data = pe.get_data(entry.struct.AddressOfRawData, entry.struct.SizeOfData)
    if data[:4] == b"RSDS":
        guid = data[4:20].hex().upper()
        age = int.from_bytes(data[20:24], "little")
        print(f"{guid}{age:x}")
        break
