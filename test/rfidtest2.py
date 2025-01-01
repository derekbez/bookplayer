from time import sleep
import nfc

with nfc.ContactlessFrontend('usb:072f:2200') as clf:

    while True:
            target = clf.sense(RemoteTarget('106A'))
            
            if target is None:
                sleep(0.1)  # don't burn the CPU
                continue

            serial = target.sdd_res.hex()

            tag = nfc.tag.activate(clf, target)

            if not tag.ndef:
                print("No NDEF records found!")
                continue
        
            for record in tag.ndef.records:
                print("Found record: " + record)

