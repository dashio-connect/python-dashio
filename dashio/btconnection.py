import gatt


class AnyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        print("Discovered [%s] %s" % (device.mac_address, device.alias()))


<<<<<<< HEAD
for bdaddr in nearby_devices:
    print (bluetooth.lookup_name( bdaddr ))

if target_address is not None:
    print ("found target bluetooth device with address ", target_address)
else:
    print ("could not find target bluetooth device nearby")
=======
manager = AnyDeviceManager(adapter_name='hci0')
manager.start_discovery()
manager.run()
>>>>>>> 507f7bf5cf4ae26bdd19f64765687811378c4dad
