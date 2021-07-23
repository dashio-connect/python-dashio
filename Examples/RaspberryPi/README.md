# Setup ble_set_wifi as a service

Edit ble_set_wifi.service so that ExecStart can find ble_set_wifi.py and ble_set_wifi.ini

```bash
sudo cp ble_set_wifi.service /etc/systemd/system
sudo systemctl enable ble_set_wifi.service
sudo systemctl start ble_set_wifi.service
```

