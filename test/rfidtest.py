import nfc

def on_connect(tag):
    print("Tag connected")
    print("UID:", tag.identifier)
    return False  # Return False to disconnect immediately after reading

# Initialize the NFC device
device = nfc.ContactlessFrontend('usb')

# Wait for a tag to be placed near the reader
device.connect(rdwr={'on-connect': on_connect})
