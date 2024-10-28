import nfc

class Reader(object):
    def __init__(self):
        try:
            self.device = nfc.ContactlessFrontend('usb')
            if not self.device:
                raise IOError("Could not initialize the device")
        except IOError as e:
            print(f"Unable to connect RFID reader: {e}")

    def read(self):
        try:
            tag = self.device.connect(rdwr={'on-connect': self.on_connect})
            return tag
        except Exception as e:
            print(f"Error reading RFID tag: {e}")
            return None

    def on_connect(self, tag):
        print("Tag connected")
        if tag.ndef or True:
            print(f"NDEF Message Length: {len(tag.ndef.records)}")
            for record in tag.ndef.records:
                print(f"Record Type: {record.type}")
                if record.type == 'urn:nfc:wkt:T':  # Text record
                    print(f"Text Record: {record.text}")
                elif record.type == 'urn:nfc:wkt:U':  # URI record
                    print(f"URI Record: {record.uri}")
                else:
                    print(f"Unknown Record: {record.data}")
        else:
            print("No NDEF records found.")
        return False

# Example Usage
if __name__ == "__main__":
    reader = Reader()
    reader.read()
