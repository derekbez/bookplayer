from smartcard.System import readers
from smartcard.util import toHexString

# Common keys for MIFARE Classic
KEYS = [
    [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],  # Default Key A
    [0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5],  # Key A
    [0xB0, 0xB1, 0xB2, 0xB3, 0xB4, 0xB5],  # Key B
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],  # NFC Tools Key
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # All zeros
]

def read_mifare():
    # Get available readers
    r = readers()
    if len(r) == 0:
        print("No readers available")
        return

    reader = r[0]
    connection = reader.createConnection()
    connection.connect()

    for sector in range(16):  # MIFARE Classic 1k has 16 sectors
        for block in range(4):  # Each sector has 4 blocks
            block_num = (sector * 4) + block
            authenticated = False

            for key in KEYS:
                auth_cmd = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block_num, 0x60, 0x00] + key
                data, sw1, sw2 = connection.transmit(auth_cmd)
                if sw1 == 0x90 and sw2 == 0x00:
                    authenticated = True
                    break

            if authenticated:
                read_cmd = [0xFF, 0xB0, 0x00, block_num, 0x10]
                data, sw1, sw2 = connection.transmit(read_cmd)
                if sw1 == 0x90 and sw2 == 0x00:
                    print(f"Block {block_num}: {toHexString(data)}")
                else:
                    print(f"Failed to read block {block_num}")
            else:
                print(f"Failed to authenticate block {block_num}")

if __name__ == "__main__":
    read_mifare()
