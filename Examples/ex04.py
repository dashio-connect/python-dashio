import dashio
import time

cfg64 = "jVTbjpswEP2VlZ9RlWS7qcQbhJCNwiUCN6lU9YEFb7ACdmrMJukq/94xhpCbqr4NZ8bj4zlz+ETOPELmz18GmrgzZH4iVpcO+aAp"\
    "WVGyr5A5NFDWfMdE1jtkImSg9H0TkQ/InQy0CEIbGnyilDMpeDF3oCZZBDbU5YRuchklknJkDr6MxgaSVBZkySsKGINKO8Q49FGb"\
    "AMB6WjD+BkBFWBay4hiyiBQkqSApRU0MVFI4OICCnO99yvzkgMz3pKggJUi2SooaSr+9GGiXCMKkJtS/Cb7hSTQpfJ6pC93Q88I1"\
    "YIeOVk/4q4H2NJP5GXkBZAv8JrzgAg5HJGu7dYitrgdy8tg8Jwgj3/IAON51H0KvUpEfDgYnJYDXKhF7ThtZK0cHvrXUgY1nbeRP"\
    "g+86wtMfWEee7enAWa3WWhUpztTWOZXkKS759pKhbcXziRIVKm0uMiIe128EzSBTlwy2YjQyrgW/mS+FZJCUqn/8uwYdrhR2YF7d"\
    "jdsNy/rZJelWUcvhhL6rE13VYtXA5ofb8sscFgmrGuHTY7Ml56QLdGP6BxgMxxqGzenBEdTC7p9fOLzgd9/0hoGaTcSVXZ5HSkov"\
    "nLWmeo1wJ+oER52GOGhlmlteI9NOkJRWjSUG15N1qahkOzDg90bEhXu8qYsvpFzOp+ifa9+tW2+iHadM9pK321szKivt9QcevnaZ"\
    "Wn6XFuct05b4D5+3j3psu3u7PI8fmfHuJ6DGj2fR8lVN+PQX"


config_dict = dashio.decode_cfg64(cfg64)
device = dashio.Device("aDeviceType", "aDeviceID2", "aDeviceName1", cfg_dict=config_dict)
tcp_con = dashio.TCPConnection()
tcp_con.add_device(device)

aknob: dashio.Knob = device.get_control(dashio.ControlName.KNOB, "aKNB")
first_dial_control: dashio.Dial = device.get_control(dashio.ControlName.DIAL, "FirstDial")


def knob_event_handler(msg):
    aknob.knob_dial_value = float(msg[3])
    first_dial_control.dial_value = float(msg[3])


aknob.add_receive_message_callback(knob_event_handler)

while True:
    time.sleep(1)
