"""
How python-dashio works: a Manim animation of a knob turned in the Dash app, from the app through
the library to your callback, and the dial update back out to every connected app.

Render (see README.md in this directory):

    manim -qh how_it_works.py HowItWorks
"""

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    DEGREES,
    PI,
    AnimationGroup,
    Arc,
    Circle,
    Create,
    DashedVMobject,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MoveAlongPath,
    RoundedRectangle,
    Scene,
    Text,
    Transform,
    ValueTracker,
    VGroup,
    VMobject,
    always_redraw,
    config,
    linear,
)

BG = "#0f172a"
FG = "#e2e8f0"
MUTED = "#64748b"
PANEL = "#1e293b"
LIB = "#60a5fa"
APP = "#4ade80"
MSG = "#fbbf24"
EVT = "#f472b6"
SANS = "Helvetica Neue"
MONO = "Menlo"

config.background_color = BG

# Layout of the frame (x from -7.1 to 7.1, y from -4 to 4)
P1 = np.array([-6.05, 1.25, 0])  # Dash app nearby, over TCP
P2 = np.array([-6.05, -2.35, 0])  # Dash app anywhere, through the Dash server
CLOUD = np.array([-4.3, -2.35, 0])
TRANSPORT_X = -2.35
TRANSPORT_Y = {"BLE": 1.0, "TCP": 0.0, "DASH": -1.0}
TRANSPORT_NAME = {"BLE": "BLEConnection", "TCP": "TCPConnection", "DASH": "DashConnection"}
RX_Y, TX_Y = 2.0, -2.0
COL = [0.25, 2.75, 5.5]  # ZMQ / Device thread / your code


def pt(x, y):
    return np.array([x, y, 0.0])


def polyline(*points, color=MUTED, opacity=0.6, width=2):
    line = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    line.set_points_as_corners([pt(*p) if len(p) == 2 else p for p in points])
    return line


def label(text, size=20, color=FG, mono=False):
    return Text(text, font=MONO if mono else SANS, font_size=size, color=color, line_spacing=0.7)


def box(text, center, width, height=0.75, color=LIB, size=18, mono=False):
    rect = RoundedRectangle(
        corner_radius=0.12,
        width=width,
        height=height,
        stroke_color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.12,
    ).move_to(center)
    txt = label(text, size, mono=mono)
    if txt.width > width - 0.2:
        txt.scale_to_fit_width(width - 0.2)
    return VGroup(rect, txt.move_to(rect))


def phone(center, width, height, title, caption):
    body = RoundedRectangle(
        corner_radius=0.22,
        width=width,
        height=height,
        stroke_color=FG,
        stroke_width=2.5,
        fill_color="#111827",
        fill_opacity=1,
    ).move_to(center)
    notch = RoundedRectangle(
        corner_radius=0.03, width=width * 0.3, height=0.06, stroke_width=0, fill_color=MUTED,
        fill_opacity=1,
    ).move_to(body.get_top() + DOWN * 0.13)
    head = label(title, 13, MUTED).move_to(body.get_top() + DOWN * 0.38)
    cap = label(caption, 15, MUTED).next_to(body, UP, buff=0.1)
    return VGroup(body, notch, head, cap)


def knob(tracker, center, r):
    base = Circle(radius=r, stroke_color=MUTED, stroke_width=2, fill_color=PANEL, fill_opacity=1)
    base.move_to(center)
    track = Arc(radius=r * 1.3, start_angle=225 * DEGREES, angle=-270 * DEGREES,
                stroke_color=MUTED, stroke_width=3, arc_center=center)

    def value_arc():
        v = max(tracker.get_value(), 0.2)
        return Arc(radius=r * 1.3, start_angle=225 * DEGREES, angle=-2.7 * v * DEGREES,
                   stroke_color=MSG, stroke_width=4, arc_center=center)

    def pointer():
        a = (225 - 2.7 * tracker.get_value()) * DEGREES
        return Line(center, center + r * 0.8 * np.array([np.cos(a), np.sin(a), 0]),
                    stroke_color=FG, stroke_width=3)

    def value():
        return label(f"{tracker.get_value():.0f}", 13).move_to(center + DOWN * (r * 1.3 + 0.12))

    return VGroup(track, always_redraw(value_arc), base, always_redraw(pointer),
                  always_redraw(value))


def dial(tracker, center, r):
    track = Arc(radius=r, start_angle=PI, angle=-PI, stroke_color=MUTED, stroke_width=5,
                arc_center=center)

    def fill():
        v = max(tracker.get_value(), 0.2)
        return Arc(radius=r, start_angle=PI, angle=-PI * v / 100, stroke_color=APP,
                   stroke_width=5, arc_center=center)

    def needle():
        a = PI - PI * tracker.get_value() / 100
        return Line(center, center + r * 0.85 * np.array([np.cos(a), np.sin(a), 0]),
                    stroke_color=FG, stroke_width=2.5)

    def value():
        return label(f"{tracker.get_value():.0f}", 13).move_to(center + DOWN * 0.15)

    return VGroup(track, always_redraw(fill), always_redraw(needle), always_redraw(value))


def cloud(center):
    puffs = VGroup(*[
        Circle(radius=r, stroke_width=0, fill_color=MUTED, fill_opacity=0.55).move_to(center + off)
        for r, off in [(0.2, pt(-0.22, -0.05)), (0.26, pt(0.02, 0.07)), (0.19, pt(0.25, -0.05))]
    ])
    return VGroup(puffs, label("Dash server", 13, MUTED).next_to(puffs, DOWN, buff=0.08))


class HowItWorks(Scene):
    def construct(self):
        self.caption = None
        self.intro()
        self.build()
        self.layout_and_connect()
        self.receive()
        self.send()
        self.history()
        self.outro()

    # Helpers

    def say(self, text, wait=0.0):
        new = label(text, 21).move_to(pt(0, -3.65))
        if new.width > 13.6:
            new.scale_to_fit_width(13.6)
        anims = [FadeIn(new, shift=UP * 0.1)]
        if self.caption is not None:
            anims.append(FadeOut(self.caption))
        self.play(*anims, run_time=0.5)
        self.caption = new
        if wait:
            self.wait(wait)

    def packets(self, routes, run_time=1.2, color=MSG):
        """Moves a labelled dot along each (text, points) route, all together."""
        movers, anims = [], []
        for text, points in routes:
            path = polyline(*points)
            dot = Dot(radius=0.08, color=color).move_to(path.get_start())
            tag = label(text, 13, color, mono=True)
            tag.add_updater(lambda m, d=dot: m.next_to(d, UP, buff=0.06))
            tag.next_to(dot, UP, buff=0.06)
            self.add(dot, tag)
            movers += [dot, tag]
            anims.append(MoveAlongPath(dot, path, rate_func=linear))
        self.play(AnimationGroup(*anims), run_time=run_time)
        for m in movers:
            m.clear_updaters()
        self.remove(*movers)

    # Routes, as lists of points

    @staticmethod
    def rx_route(name):
        y = TRANSPORT_Y[name] + 0.12
        return [(-1.6, y), (-1.3, y), (-1.3, RX_Y), (COL[0] - 1.0, RX_Y)]

    @staticmethod
    def tx_route(name):
        y = TRANSPORT_Y[name] - 0.12
        return [(COL[0] - 1.0, TX_Y), (-1.05, TX_Y), (-1.05, y), (-1.6, y)]

    @staticmethod
    def app_route(name, inbound):
        if name == "TCP":
            pts = [(P1[0] + 0.85, 0.0), (-3.1, 0.0)]
        else:
            pts = [(P2[0] + 0.75, P2[1]), (CLOUD[0] - 0.45, CLOUD[1]),
                   (CLOUD[0] + 0.45, CLOUD[1]), (-3.1, -1.0)]
        return pts if inbound else pts[::-1]

    # Sections

    def intro(self):
        title = label("python-dashio", 64)
        sub = label("How a Python program talks to the Dash app", 28, MUTED)
        VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(FadeIn(title, shift=UP * 0.2), FadeIn(sub), run_time=1.0)
        self.wait(1.5)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.6)

    def build(self):
        # The apps
        self.k1, self.d1, self.d2 = ValueTracker(0), ValueTracker(0), ValueTracker(0)
        p1 = phone(P1, 1.7, 3.1, "aDeviceName", "Dash app, nearby")
        p2 = phone(P2, 1.5, 1.7, "aDeviceName", "Dash app, anywhere")
        self.p1_controls = VGroup(knob(self.k1, P1 + UP * 0.45, 0.33),
                                  dial(self.d1, P1 + DOWN * 0.85, 0.45))
        self.p2_controls = dial(self.d2, P2 + DOWN * 0.3, 0.38)
        server = cloud(CLOUD)

        # The computer
        computer = RoundedRectangle(corner_radius=0.2, width=10.45, height=6.5, stroke_color=FG,
                                    stroke_width=2, fill_color=PANEL, fill_opacity=0.35)
        computer.move_to(pt(1.725, 0))
        computer_title = label("Your computer or Raspberry Pi, running Python", 20, FG)
        computer_title.next_to(computer, UP, buff=0.1).align_to(computer, LEFT)
        lib = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=7.45, height=5.85,
                                              stroke_color=LIB, stroke_width=1.5),
                             num_dashes=70).move_to(pt(0.325, -0.18))
        lib_title = label("dashio", 17, LIB).move_to(pt(-2.5, 2.95))
        app = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=2.6, height=5.85,
                                              stroke_color=APP, stroke_width=1.5),
                             num_dashes=40).move_to(pt(5.5, -0.18))
        app_title = label("your code", 17, APP).move_to(pt(5.5, 2.95))

        self.transports = {
            name: box(TRANSPORT_NAME[name], pt(TRANSPORT_X, y), 1.5, 0.55, color=LIB, size=15)
            for name, y in TRANSPORT_Y.items()
        }
        links = VGroup(
            polyline(*self.app_route("TCP", True), opacity=0.8),
            polyline(*self.app_route("DASH", True), opacity=0.8),
        )

        self.play(FadeIn(computer), FadeIn(computer_title), run_time=0.6)
        self.play(FadeIn(p1), FadeIn(p2), FadeIn(server), run_time=0.6)
        self.play(*[FadeIn(t) for t in self.transports.values()], Create(links), run_time=0.8)
        self.say("The Dash app reaches the device over your local network (TCP), through the "
                 "Dash server, or over Bluetooth LE on Linux.", wait=1.5)
        ble = self.transports["BLE"]
        self.play(ble.animate.set_opacity(0.35), run_time=0.5)
        self.say("Each connection runs in its own thread. Add the device to the ones you want: "
                 "here TCP and the Dash server.", wait=1.8)

        self.zmq_rx = box("ZMQ", pt(COL[0], RX_Y), 2.0)
        self.device = box("Device thread\n_on_message()", pt(COL[1], RX_Y), 1.9)
        self.handler = box("knob_event_handler(msg)", pt(COL[2], RX_Y), 2.3, color=APP, mono=True)
        self.zmq_tx = box('ZMQ\npublish "ALL"', pt(COL[0], TX_Y), 2.0)
        self.control = box("Dial dial1\nstate_str", pt(COL[1], TX_Y), 1.9)
        self.setter = box("dial_value = ...", pt(COL[2], TX_Y), 2.3, color=APP, mono=True)
        wires = VGroup(
            *[polyline(*self.rx_route(n), opacity=0.45) for n in TRANSPORT_Y],
            *[polyline(*self.tx_route(n), opacity=0.45) for n in TRANSPORT_Y],
            polyline((COL[0] + 1.0, RX_Y), (COL[1] - 0.95, RX_Y)),
            polyline((COL[1] + 0.95, RX_Y), (COL[2] - 1.15, RX_Y)),
            polyline((COL[2] - 1.15, TX_Y), (COL[1] + 0.95, TX_Y)),
            polyline((COL[1] - 0.95, TX_Y), (COL[0] + 1.0, TX_Y)),
        )
        self.play(Create(lib), FadeIn(lib_title), Create(app), FadeIn(app_title), run_time=0.8)
        self.play(*[FadeIn(b) for b in (self.zmq_rx, self.device, self.zmq_tx, self.control)],
                  FadeIn(wires), run_time=0.8)
        self.play(FadeIn(self.handler), FadeIn(self.setter), run_time=0.6)
        self.say("The connections and the Device talk over ZMQ. Your code creates the controls, "
                 "and handles their messages.", wait=2.0)

    def layout_and_connect(self):
        source = box("Your controls,\nor cfg_dict", pt(0.3, 0), 1.7, 0.75, color=MUTED)
        cfg = box("CFG64", pt(2.7, 0), 1.5, 0.55, color=MUTED, mono=True)
        arrow = polyline((1.2, 0), (1.9, 0), color=FG, opacity=0.8)
        self.say("The layout is generated from your controls, or designed in the Dash app, "
                 "exported, and loaded with cfg_dict.")
        self.play(FadeIn(source), run_time=0.5)
        self.play(Create(arrow), FadeIn(cfg, shift=RIGHT * 0.2), run_time=0.7)
        self.wait(0.8)
        self.layout = box("layout", pt(COL[1], 0.45), 1.1, 0.42, color=LIB, size=14)
        self.play(FadeOut(source), FadeOut(arrow), Transform(cfg, self.layout), run_time=0.8)

        self.say("On connecting, the app asks WHO, then the layout (CFG) if it hasn't got "
                 "this cfgRev, then STATUS.")
        tcp_in = self.app_route("TCP", True) + self.rx_route("TCP") + [(COL[1] - 0.95, RX_Y)]
        down = [(COL[1], RX_Y - 0.38), (COL[1], TX_Y + 0.38)]
        out = [(COL[1] - 0.95, TX_Y), (COL[0] + 1.0, TX_Y)]
        out_tcp = [(COL[0] - 1.0, TX_Y)] + self.tx_route("TCP")[1:] + self.app_route("TCP", False)
        for ask, reply, then in (("WHO", "WHO, cfgRev 1", None),
                                 ("CFG", "CFG: layout", "layout"),
                                 ("STATUS", "NAME, PKG", None)):
            self.packets([(ask, tcp_in)], run_time=1.0)
            if then:
                self.play(Indicate(cfg, color=MSG), run_time=0.5)
            self.packets([(reply, down)], run_time=0.4)
            self.packets([(reply, out)], run_time=0.4)
            self.packets([(reply, out_tcp)], run_time=1.0)
            if then:
                self.play(FadeIn(self.p1_controls), FadeIn(self.p2_controls), run_time=0.6)
        self.wait(0.6)

    def receive(self):
        self.say("Turn the knob, and the app sends the new value.")
        self.play(self.k1.animate.set_value(42), run_time=1.2)
        self.packets([("KNOB aKNB 42", self.app_route("TCP", True) + self.rx_route("TCP"))],
                     run_time=1.6)

        self.say("The TCPConnection passes it over ZMQ to the Device thread, which splits it "
                 "on tabs.")
        self.packets([("aKNB 42", [(COL[0] + 1.0, RX_Y), (COL[1] - 0.95, RX_Y)])], run_time=0.6)
        tokens = VGroup(*[box(t, pt(0, 0), w, 0.36, color=MSG, size=13, mono=True)
                          for t, w in (("KNOB", 0.7), ("aKNB", 0.7), ("42", 0.45))])
        tokens.arrange(RIGHT, buff=0.08).move_to(pt(COL[1], RX_Y - 0.72))
        self.play(Indicate(self.device, color=MSG), FadeIn(tokens, shift=DOWN * 0.1), run_time=0.8)
        self.wait(0.8)

        self.say("It finds the Knob aKNB, and calls the callbacks you added to it.")
        self.packets([("aKNB 42", [(COL[1] + 0.95, RX_Y), (COL[2] - 1.15, RX_Y)])], run_time=0.6)
        added = label("aknob.add_receive_message_callback(\n  knob_event_handler)", 11, APP,
                      mono=True)
        added.scale_to_fit_width(2.3).move_to(pt(COL[2], RX_Y - 0.62))
        value = label('msg[3] == "42"', 13, APP, mono=True).move_to(pt(COL[2], RX_Y - 1.1))
        self.play(FadeOut(tokens), FadeIn(added), run_time=0.5)
        self.play(Indicate(self.handler, color=APP), FadeIn(value), run_time=0.8)
        self.wait(1.2)
        self.play(FadeOut(value), FadeOut(added), run_time=0.3)

    def send(self):
        self.say("Your callback sets the dial's value. The Dial sends it to the Device...")
        code = label("first_dial_control.dial_value = float(msg[3])", 11, APP, mono=True)
        code.scale_to_fit_width(2.3).move_to(pt(COL[2], TX_Y + 0.62))
        self.play(FadeIn(code), run_time=0.4)
        self.packets([("dial1 42", [(COL[2], RX_Y - 0.38), (COL[2], TX_Y + 0.38)])],
                     run_time=0.8, color=APP)
        self.packets([("DIAL dial1 42", [(COL[2] - 1.15, TX_Y), (COL[1] + 0.95, TX_Y)])],
                     run_time=0.6, color=APP)
        self.play(Indicate(self.control, color=MSG), FadeOut(code), run_time=0.6)

        self.say('...which publishes it on ZMQ to "ALL": every connection the device is on.')
        self.packets([("DIAL dial1 42", [(COL[1] - 0.95, TX_Y), (COL[0] + 1.0, TX_Y)])],
                     run_time=0.6)
        self.play(Indicate(self.zmq_tx, color=MSG), run_time=0.5)
        self.packets([("DIAL dial1 42", self.tx_route("TCP")),
                      ("DIAL dial1 42", self.tx_route("DASH"))], run_time=0.9)
        self.packets([("DIAL dial1 42", self.app_route("TCP", False))], run_time=0.8)
        self.play(self.d1.animate.set_value(42), run_time=0.7)

        note = label("an app watching?\nbatch for 50 ms", 12, MSG).next_to(
            self.transports["DASH"], DOWN, buff=0.12)
        self.say("The DashConnection only publishes updates while an app is watching, and "
                 "batches what's sent within 50 ms.")
        self.play(FadeIn(note), Indicate(self.transports["DASH"], color=MSG), run_time=0.8)
        self.packets([("DIAL dial1 42", self.app_route("DASH", False))], run_time=1.0)
        self.play(self.d2.animate.set_value(42), run_time=0.7)
        self.wait(1.0)
        self.play(FadeOut(note), run_time=0.4)

    def history(self):
        store = box("DashStore\nsqlite", pt(COL[1], -0.55), 1.9, color=EVT)
        point = box("add_data_point()", pt(COL[2], -0.55), 2.3, color=APP, mono=True)
        wire = polyline((COL[2] - 1.15, -0.55), (COL[1] + 0.95, -0.55), opacity=0.45)
        self.say("Time graph, event log and map history can go in a DashStore, so it survives "
                 "a restart, or the connection being down.")
        self.play(FadeIn(store), FadeIn(point), FadeIn(wire), run_time=0.6)
        for value in ("21.5", "21.7"):
            self.packets([(value, [(COL[2] - 1.15, -0.55), (COL[1] + 0.95, -0.55)])],
                         run_time=0.6, color=EVT)
            self.play(Indicate(store, color=EVT), run_time=0.4)

        self.say("When the device connects, it uploads what the Dash server is missing, "
                 "a packet at a time, each one ACKed.")
        to_server = [(COL[1] - 0.95, -0.55), (-1.3, -0.55), (-1.3, -0.88), (-1.6, -0.88)]
        to_cloud = self.app_route("DASH", False)[:3]
        back = to_cloud[::-1]
        for ask, reply in (("SDU REQUEST", "REQUEST: ts"), ("SDU UPDATE", "ACK")):
            self.packets([(ask, to_server)], run_time=0.8, color=EVT)
            self.packets([(ask, to_cloud)], run_time=0.8, color=EVT)
            self.packets([(reply, back)], run_time=0.8, color=EVT)
        self.wait(0.6)

    def outro(self):
        self.say("All of it in plain Python: pip install dashio.", wait=2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        end = VGroup(label("python-dashio", 48),
                     label("github.com/dashio-connect/python-dashio", 24, MUTED, mono=True))
        end.arrange(DOWN, buff=0.3)
        self.play(FadeIn(end), run_time=0.8)
        self.wait(2.0)
