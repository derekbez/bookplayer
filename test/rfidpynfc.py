import pynfc

def on_connect(tag):
    print("Tag connected")
    print(f"UID: {tag.uid.hex()}")

    if hasattr(tag, 'type'):
        print(f"Tag Type: {tag.type}")

    key_a = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
    for sector in range(16):  # MIFARE Classic 1k has 16 sectors
        print(f"Reading sector {sector}:")
        for block in range(4):  # Each sector has 4 blocks
            block_number = sector * 4 + block
            try:
                if tag.authenticate(key_a, block_number):
                    data = tag.read_block(block_number)
                    print(f"  Block {block_number}: {data.hex()}")
                else:
                    print(f"  Failed to authenticate block {block_number}")
            except Exception as e:
                print(f"  Failed to read block {block_number}: {e}")

reader = pynfc.Reader()
reader.connect(rdwr={'on-connect': on_connect})
