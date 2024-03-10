import serial
import time
from enum import Enum


class LTE_State(Enum):
    MODULE_STARTUP = 0
    SIM_READY = 1
    LTE_DISCONNECTED = 2
    LTE_CONNECTED = 3
    MODULE_REQ_RESET = 4
    MODULE_RESETTING = 5
    MODULE_REQ_SHUTDOWN = 6
    MODULE_SHUTTING_DOWN = 7
    MODULE_SHUTDOWN = 8


class MQTT_State(Enum):
    MQTT_DISCONNECTED = 0
    MQTT_REQ_CONNECT = 1
    MQTT_CONNECTING = 2
    MQTT_REQ_SUBSCRIBE = 3
    MQTT_SUBSCRIBING = 4
    MQTT_CONNECTED = 5
    MQTT_REQ_DISCONNECT = 6
    MQTT_DISCONNECTING = 7


class GNSS_State(Enum):
    GNSS_OFF = 0
    GNSS_REQ_POWERUP = 1
    GNSS_POWERING_UP = 2
    GNSS_REQ_DATA = 3
    GNSS_REQ_SHUTDOWN = 4
    GNSS_SHUTDOWN = 5


class ERROR_State(Enum):
    ERR_NONE = 0
    ERR_REBOOT = 1
    ERR_STARTUP_TIMEOUT = 2
    ERR_NO_CARRIER_TIMEOUT = 3
    ERR_LTE_CONNECT_FAIL_RESET = 4
    ERR_LTE_DISCONNECT_RESET = 5
    ERR_MQTT_RECONNECT_FAIL_RESET = 6
    ERR_MQTT_CONNECTION_LOST = 7
    ERR_AT_TIMEOUT_RESET = 8


class SIM767X:
    MAX_MESSAGE_LEN = 10000
    CHECK_CONNECTION_INTERVAL_S = 30
    SHUTDOWN_WAIT_S = 20

    printMessages = True
    autoShutdown = False
    onOKCallback = None
    onEnterCallback = None

    receiveIncomingMessageCallback = None
    onNewDeviceIDcallback = None
    mqttConnectCallback = None
    mqttPublishCallback = None

    checkConnectionSecondCount = 0
    atTimeoutS = 10
    chars = ""
    incomingMessage = False
    moreDataComing = 0

    startTime = time.time()

    txMessage = ""
    rxMessage = ""

    atTimeoutS = 10
    atTimerS = -1
    shutDownTimerS = -1
    mqttReconnectTimerS = -1
    disconnectTimerS = 0
    runATcallbacks = False

    lteState = LTE_State.MODULE_STARTUP
    errorState = ERROR_State.ERR_REBOOT
    mqttState = MQTT_State.MQTT_DISCONNECTED

    mqttIsPublishing = False
    willSubTopic = ""
    willSubMessage = ""
    topic = ""
    messageToSend = ""
    messageSendID = -1
    alarmMessageToSend = ""
    announceMessageToSend = ""
    lastCommand = ""

    username = ""
    password = ""

    gnssDataCallback = None
    gnssInterval = 60
    gnssOneShot = False
    gnssIntervalTimerS = 0
    gnssRetryCounter = 0
    gnssState = GNSS_State.GNSS_SHUTDOWN

    def __init__(self, _serial, _deviceID, _network, _apn):
        self.deviceID = _deviceID
        self.network = _network
        self.apn = _apn
        self.serialAT = serial.Serial(_serial, 115200)

    def setup(self, _username, _password):
        self.username = _username
        self.password = _password

    def setCallbacks(self, _onMQTTconnect, _receiveIncomingMessage, _onNewDeviceID):
        self.onMQTTconnect = _onMQTTconnect
        self.receiveIncomingMessageCallback = _receiveIncomingMessage
        self.onNewDeviceIDcallback = _onNewDeviceID

    def sendAnnounce(self, announceMessage):
        if len(self.announceMessageToSend) + len(announceMessage) <= self.MAX_MESSAGE_LEN:
            self.announceMessageToSend += announceMessage

    def sendAlarm(self, alarmMessage):
        if len(self.alarmMessageToSend) + len(alarmMessage) <= self.MAX_MESSAGE_LEN:
            self.alarmMessageToSend += alarmMessage

    def sendMessage(self, message, messageID):
        if len(self.messageToSend) + len(message) <= self.MAX_MESSAGE_LEN:
            self.messageToSend += message
            if (messageID > 0):  # Allow for multiple messages, where some may have no messageID
                self.messageSendID = messageID

    def log(self, message):
        print(message)

    def protectedATcmd(self, cmd, _onOKCallback, _onEnterCallback, _timeoutS=10):
        if not self.runATcallbacks:
            self.onOKCallback = _onOKCallback
            self.onEnterCallback = _onEnterCallback
            self.atTimeoutS = _timeoutS
            self.runATcallbacks = True

            command = "AT+" + cmd + "\r\n"
            self.serialAT.write(command.encode())

            return True
        else:
            return False

    def resetTimers(self):
        self.atTimerS = -1
        self.mqttReconnectTimerS = -1
        self.shutDownTimerS = -1

        self.mqttIsPublishing = False
        self.mqttState = MQTT_State.MQTT_DISCONNECTED
        self.gnssState = GNSS_State.GNSS_OFF

    def onMQTTconnected(self):
        self.mqttState = MQTT_State.MQTT_CONNECTED

        # Send MQTT ONLINE and WHO messages to connection
        # WHO is only required here if using the Dash server and it must be sent to the ANNOUNCE topic
        self.sendMessage(self.getOnlineMessage(), -1)

        if self.mqttConnectCallback is not None:
            self.mqttConnectCallback(True, self.errorState)

        self.errorState = ERROR_State.ERR_NONE

    def getOnlineMessage(self):
        return "\t" + self.deviceID + "\tONLINE\n"

    def getOfflineMessage(self):
        return "\t" + self.deviceID + "\tOFFLINE\n"

    def getMQTTTopic(self, username, topic):
        return username + "/" + self.deviceID + "/" + topic

    def run(self):
        self.processATcommands()
        self.checkOutgoingMessages()

        now = time.time()
        deltaTime = now - self.startTime
        if deltaTime >= 1:
            self.startTime = now

            self.runOneSecondModuleTasks()
            self.runOneSecondMQTTTasks()
            self.runOneSecondGNSSTasks()

            if self.autoShutdown and (self.lteState == LTE_State.LTE_CONNECTED) and (self.mqttState == MQTT_State.MQTT_CONNECTED):
                if (self.gnssDataCallback is None or self.gnssState == GNSS_State.GNSS_SHUTDOWN):
                    if len(self.messageToSend) == 0 and len(self.alarmMessageToSend) == 0 and len(self.announceMessageToSend) == 0:
                        if not self.runATcallbacks:
                            self.powerDownModule()

    def processATcommands(self):
        while self.serialAT.in_waiting > 0:
            if self.moreDataComing > 0:  # Required because we can read the message through AT faster than it may arrive.
                self.readMessage(self.moreDataComing)
            else:
                data = ""
                haveMessage = False
                while self.serialAT.in_waiting > 0 and not haveMessage:
                    charsIn = self.serialAT.read().decode()
                    if '\n' in charsIn:
                        charsArr = charsIn.split('\n')
                        self.chars += charsArr[0]
                        data = self.chars
                        self.chars = ""
                        haveMessage = True
                        break
                    else:
                        self.chars += charsIn
                        if self.chars.startswith(">"):
                            data = ">"
                            self.chars = ""
                            haveMessage = True

                data = data.replace('\r', '')

                if (haveMessage or data.startswith(">")) and (len(data) > 0):
                    if (self.printMessages):
                        print("CMD: " + data)

                    if data.startswith("OK"):
                        if (self.printMessages):
                            print()

                        if self.runATcallbacks:
                            self.runATcallbacks = False
                            if (self.onOKCallback is not None):
                                self.onOKCallback()
                    elif (data.startswith("ERROR")):
                        self.moreDataComing = 0  # Just in case
                        if (self.runATcallbacks):
                            self.runATcallbacks = False
                            if (self.printMessages):
                                print("Callback - Houston - we have a problem ERROR")
                            self.log("AT Error")
                    elif data.startswith(">"):
                        if self.runATcallbacks:
                            if (self.onEnterCallback is not None):
                                self.onEnterCallback()
                    else:
                        dataArr = data.split(':')
                        if len(dataArr) > 1:
                            resultStr = dataArr[1]
                            resultStr = resultStr.strip()

                        if data.startswith("+CPIN:"):
                            if (resultStr.startswith("READY")):  # Module has started up and is ready for AT commands
                                self.runATcallbacks = False
                                self.lteState = LTE_State.SIM_READY

                        elif (data.startswith("+CREG:")) or (data.startswith("+CEREG:")) or (data.startswith("+CGREG:")):  # Network Registration Status
                            resultArr = resultStr.split(',')
                            if len(resultArr) == 1:  # Unsolicited response
                                status = int(resultArr[0])
                                if (status == 1) or (status == 5):
                                    if (self.lteState != LTE_State.LTE_CONNECTED):
                                        self.lteState = LTE_State.LTE_CONNECTED
                                        self.disconnectTimerS = 0
                                        self.startPDPContext()
                            else:  # Request response
                                status = int(resultArr[1])
                                if (status == 1) or (status == 5):
                                    if (self.lteState != LTE_State.LTE_CONNECTED):
                                        self.lteState = LTE_State.LTE_CONNECTED
                                        self.disconnectTimerS = 0
                                        self.startPDPContext()
                                else:  # Only do this for request response (i.e. when monitoring)
                                    self.lteState = LTE_State.LTE_DISCONNECTED
                                    self.mqttState = MQTT_State.MQTT_DISCONNECTED
                                    self.errorState = ERROR_State.ERR_LTE_CONNECT_FAIL_RESET
                        elif data.startswith("+CGEV:"):
                            if (resultStr.startswith("ME PDN ACT")):  # AcT = 0 (GSM)
                                self.log("ME PDN ACT")
                            elif (resultStr.startswith("EPS PDN ACT")):  # AcT = 7 (EUTRAN)
                                self.log("EPS PDN ACT")
                            elif (resultStr.startswith("ME PDN DEACT")):
                                self.log("ME PDN DEACT")
                            elif (resultStr.startswith("NW PDN DEACT")):
                                self.log("NW PDN DEACT")
                        elif data.startswith("+SIMEI:"):
                            if self.deviceID is None:
                                self.deviceID = "IMEI" + resultStr
                            if (self.onNewDeviceIDcallback is not None):
                                self.onNewDeviceIDcallback(self.deviceID)
                        elif data.startswith("+COPS:"):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 3:
                                self.log("Carrier: " + resultArr[2])
                        # MQTT
                        elif (data.startswith("+CMQTTSTART:")):
                            error = int(resultStr)
                            if (error == 0):
                                self.mqttAcquireCLient()
                            else:
                                self.log("MQTT Start: " + str(error))
                                self.lteState = LTE_State.MODULE_REQ_RESET
                        elif (data.startswith("+CMQTTCONNECT:")):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if (error == 0):
                                    self.mqttState = MQTT_State.MQTT_REQ_SUBSCRIBE
                                    self.mqttReconnectFailCounter = 0
                                else:
                                    self.log("MQTT Cnct: " + str(error))
                                    self.reqMQTTreconnect()
                        elif data.startswith("+CMQTTSUB:"):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if error == 0:
                                    self.onMQTTconnected()
                                else:
                                    self.log("MQTT Sub: " + str(error))
                                    self.reqMQTTreconnect()
                        elif data.startswith("+CMQTTPUB:"):
                            self.mqttIsPublishing = False

                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if self.mqttPublishCallback is not None:
                                    self.mqttPublishCallback(self.topic, self.messageSendID, error)  # Do before topic is cleared below
                                self.messageSendID = -1  # Probably don't need this

                                if error != 0:
                                    self.log("MQTT Pub: " + str(error))
                                    self.reqMQTTreconnect()
                                else:
                                    self.topic = ""
                                    self.txMessage = ""
                        elif data.startswith("+CMQTTRXTOPIC:"):
                            # No need to do anything with the received topic as there shoud only be one topic.
                            pass
                        elif data.startswith("+CMQTTRXSTART:"):
                            self.incomingMessage = True
                            self.rxMessage = ""
                        elif data.startswith("+CMQTTRXPAYLOAD:"):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                self.readMessage(int(resultArr[1]))
                        elif data.startswith("+CMQTTRXEND:"):
                            self.moreDataComing = 0
                            self.incomingMessage = False

                            if len(self.rxMessage) > 0:
                                if self.receiveIncomingMessageCallback is not None:
                                    self.receiveIncomingMessageCallback(self.rxMessage)
                                self.rxMessage = ""
                        elif data.startswith("+CMQTTDISC:"):
                            self.mqttState = MQTT_State.MQTT_DISCONNECTED
                            if self.shutDownTimerS >= 0:
                                self.lteState = LTE_State.MODULE_REQ_SHUTDOWN
                        elif data.startswith("+CMQTTCONNLOST:"):
                            self.mqttState = MQTT_State.MQTT_DISCONNECTED
                            if self.mqttConnectCallback is not None:
                                self.mqttConnectCallback(False, ERROR_State.ERR_MQTT_CONNECTION_LOST)

                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                self.log("MQTT Cnct Lost: " + str(error))
                                self.reqMQTTreconnect()
                        # GNSS
                        elif data.startswith("+CGNSSINFO:"):
                            self.processGNSSdata(resultStr)

    def readMessage(self, messageLen):
        charsIn = self.serialAT.read().decode()
        self.rxMessage += charsIn
        self.moreDataComing = messageLen - len(charsIn)

    def runOneSecondModuleTasks(self):
        if self.shutDownTimerS >= 0:
            if self.printMessages:
                print(str(self.shutDownTimerS) + "s")
            self.shutDownTimerS += 1
            if (self.shutDownTimerS == self.SHUTDOWN_WAIT_S):
                self.mqttState = MQTT_State.MQTT_REQ_DISCONNECT
            if (self.shutDownTimerS == self.SHUTDOWN_WAIT_S + 5):  # Allow 5 seconds to disconnect before shutdown
                self.shutDownTimerS = -1  # Turn off timer
                self.lteState = LTE_State.MODULE_REQ_SHUTDOWN

        # LTE State
        if self.lteState == LTE_State.MODULE_STARTUP:
            if self.printMessages:
                print(str(self.disconnectTimerS) + ".")
            self.disconnectTimerS += 1
            if (self.disconnectTimerS > 60):  # One min
                self.disconnectTimerS = 0
                self.runATcallbacks = False
                self.reqResetModule(ERROR_State.ERR_STARTUP_TIMEOUT)
        elif self.lteState == LTE_State.SIM_READY:
            self.lteState = LTE_State.LTE_DISCONNECTED
            self.resetTimers()
            self.disconnectTimerS = 0

            self.getIMEI()
        elif self.lteState == LTE_State.LTE_DISCONNECTED:
            if self.printMessages:
                print(str(self.disconnectTimerS) + "^")
            self.disconnectTimerS += 1
            if (self.disconnectTimerS > 300):  # Five mins
                self.disconnectTimerS = 0
                self.reqResetModule(ERROR_State.ERR_NO_CARRIER_TIMEOUT)
        elif self.lteState == LTE_State.MODULE_REQ_RESET:
            self.resetModule()
        elif self.lteState == LTE_State.MODULE_REQ_SHUTDOWN:
            self.shutdownModule()

        # Check Connection
        self.checkConnectionSecondCount += 1
        if (self.checkConnectionSecondCount > self.CHECK_CONNECTION_INTERVAL_S):
            self.checkConnectionSecondCount = 0
            if self.lteState == LTE_State.LTE_CONNECTED:
                self.checkConnection()

        if self.runATcallbacks:
            if self.atTimerS >= 0:  # i.e. -1 is timer turned off
                self.atTimerS += 1
                if self.atTimerS > self.atTimeoutS:
                    self.atTimerS = -1  # Turn off timer
                    self.runATcallbacks = False
                    if self.printMessages:
                        print("Callback - Houston - we have a problem TIMEOUT")
                    self.timeoutErrorCommand = self.lastCommand
                    self.reqResetModule(ERROR_State.ERR_AT_TIMEOUT_RESET)

    def runOneSecondMQTTTasks(self):
        if self.mqttState == MQTT_State.MQTT_REQ_CONNECT:
            self.mqttConnect()
        elif self.mqttState == MQTT_State.MQTT_REQ_SUBSCRIBE:
            self.mqttReqSubscribe()
        elif self.mqttState == MQTT_State.MQTT_REQ_DISCONNECT:
            self.mqttDisconnect()

        if self.mqttReconnectTimerS >= 0:
            self.mqttReconnectTimerS += 1
            if self.printMessages:
                print(str(self.mqttReconnectTimerS) + "m")
            if self.mqttReconnectTimerS >= 10:
                self.mqttReconnectTimerS = -1  # Turn off timer
                self.log("MQTT Reconnect")
                self.reqMQTTconnect()

    def runOneSecondGNSSTasks(self):
        if self.gnssState == GNSS_State.GNSS_REQ_POWERUP:
            self.powerUpGNSS()
        elif self.gnssState == GNSS_State.GNSS_REQ_DATA:
            self.gnssIntervalTimerS += 1
            if self.printMessages:
                print(str(self.gnssIntervalTimerS) + "g")
            if self.gnssIntervalTimerS >= self.gnssInterval:
                self.gnssIntervalTimerS = 0
                self.getGNSSinfo()
        elif self.gnssState == GNSS_State.GNSS_REQ_SHUTDOWN:
            self.powerDownGNSS()

    def checkOutgoingMessages(self):
        if (not self.mqttIsPublishing) and (self.mqttState == MQTT_State.MQTT_CONNECTED) and (not self.runATcallbacks):
            if not self.incomingMessage:  # Wait if any received message is being downloaded.
                if (len(self.topic) > 0) and (len(self.txMessage) > 0):
                    self.mqttRequestPublish()  # Try and publish again
                elif len(self.messageToSend) > 0:  # Don't send a message unless all callbacks are finished.
                    self.txMessage = self.messageToSend
                    self.topic = self.getMQTTTopic(self.username, "data")
                    if self.mqttRequestPublish():
                        self.messageToSend = ""
                elif len(self.alarmMessageToSend) > 0:
                    self.txMessage = self.alarmMessageToSend
                    self.topic = self.getMQTTTopic(self.username, "alarm")
                    if (self.mqttRequestPublish()):
                        self.alarmMessageToSend = ""
                elif len(self.announceMessageToSend) > 0:
                    self.txMessage = self.announceMessageToSend
                    self.topic = self.getMQTTTopic(self.username, "announce")
                    if self.mqttRequestPublish():
                        self.announceMessageToSend = ""

    def powerDownModule(self):
        self.lteState = LTE_State.MODULE_SHUTTING_DOWN
        self.messageToSend = self.getOfflineMessage()
        self.shutDownTimerS = 0  # Start shutdown counter

    def shutdownModule(self):
        if self.protectedATcmd("CPOF", lambda: self.resetTimers(), lambda: None, 120):
            self.shutDownTimerS = -1
            self.lteState = LTE_State.MODULE_SHUTDOWN

    def reqResetModule(self, _errorState):
        self.errorState = _errorState
        self.lteState = LTE_State.MODULE_REQ_RESET

    def resetModule(self):
        if self.protectedATcmd("CRESET", lambda: self.resetTimers(), lambda: None, 120):
            self.lteState = LTE_State. MODULE_RESETTING

    def printOK(self):
        if self.printMessages:
            print("OK ACK")

    def checkConnection(self):
        self.protectedATcmd("CREG?", lambda: self.printOK(), lambda: None)

    def getIMEI(self):
        self.protectedATcmd("SIMEI?", lambda: self.setUnsolicitedNetworkRegMessages(), lambda: None)

    def setUnsolicitedNetworkRegMessages(self):
        self.protectedATcmd("CREG=1", lambda: self.setCarrier, lambda: None)

    def setCarrier(self):
        if self.network is not None:
            carrierStr = "AT+COPS=4,2,\""  # 1 = manual (4 = manual/auto), 2 = short format. For One NZ SIM cards not roaming in NZ, Could take up to 60s
            carrierStr += self.network
            carrierStr += "\""
            self.serialAT.write(carrierStr.encode())  # ??? Maybe should be protected

    def startPDPContext(self):
        contextStr = "CGDCONT=1,\"IP\",\""
        contextStr += self.apn
        contextStr += "\""
        self.protectedATcmd(contextStr, lambda: self.activateContext(), lambda: None)

    def activateContext(self):
        self.protectedATcmd("CGACT=1,1", lambda: self.getCarrier(), lambda: None)

    def getCarrier(self):
        self.protectedATcmd("COPS?", lambda: self.mqttStart(), lambda: None)

# ----- MQTT -----
    def reqMQTTreconnect(self):
        self.mqttIsPublishing = False
        self.mqttState = MQTT_State.MQTT_DISCONNECTED

        self.mqttReconnectFailCounter += 1
        if self.mqttReconnectFailCounter > 5:  # After 5 tries, go for a reset
            self.mqttReconnectFailCounter = 0
            self.reqResetModule(ERROR_State.ERR_MQTT_RECONNECT_FAIL_RESET)
        else:
            self.mqttReconnectTimerS = 0  # Restart timer

    def mqttDisconnect(self):
        if self.protectedATcmd("CMQTTDISC=0,60", lambda: self.printOK(), lambda: None):  # clientIndex = 0, timeout (force disconnect to attempt to clear out any buffers etc.)
            self.mqttState = MQTT_State.MQTT_DISCONNECTING

    def mqttStart(self):
        self.protectedATcmd("CMQTTSTART", lambda: self.printOK(), lambda: None, 60)

    def mqttAcquireCLient(self):
        tempStr = "CMQTTACCQ=0,\""  # clientIndex = 0
        tempStr += self.deviceID  # cliendID
        tempStr += "\",1"  # serverType 1 = SSL/TLS, 0 = TCP
        self.protectedATcmd(tempStr, lambda: self.mqttConfigSSL(), lambda: None)

    def mqttConfigSSL(self):
        self.protectedATcmd("CMQTTSSLCFG=0,0", lambda: self.mqttRequestWillToic(), lambda: None)  # sessionID = 0, sslIndex = 0

# ---- MQTT LWT -----
    def mqttRequestWillToic(self):
        self.willSubTopic = self.getMQTTTopic(self.username, "data")
        self.willSubMessage = self.getOfflineMessage()
        self.protectedATcmd("CMQTTWILLTOPIC=0," + str(len(self.willSubTopic)), lambda: self.mqttRequestWillMessage(), lambda: self.mqttEnterWillToic())  # clientIndex = 0

    def mqttEnterWillToic(self):
        self.serialAT.write((self.willSubTopic).encode())

    def mqttRequestWillMessage(self):
        tempStr = "CMQTTWILLMSG=0,"
        tempStr += str(len(self.willSubMessage))
        tempStr += ",2"
        self.protectedATcmd(tempStr, lambda: self.reqMQTTconnect(), lambda: self.mqttEnterWillMessage())  # clientIndex = 0, qos = 2

    def mqttEnterWillMessage(self):
        self.serialAT.write(self.willSubMessage.encode())

    def reqMQTTconnect(self):
        self.mqttState = MQTT_State.MQTT_REQ_CONNECT

# ---- MQTT Connect -----
    def mqttConnect(self):
        connectStr = "CMQTTCONNECT=0,\"tcp://dash.dashio.io:8883\",60,1,\""  # 60s keep alive
        connectStr += self.username
        connectStr += "\",\""
        connectStr += self.password
        connectStr += "\""
        if self.protectedATcmd(connectStr, lambda: self.printOK(), lambda: None, 60):  # Allow 60s for MQTT to connect
            self.mqttState = MQTT_State.MQTT_CONNECTING

# ---- MQTT Subscribe -----
    def mqttReqSubscribe(self):
        self.willSubTopic = self.getMQTTTopic(self.username, "control")
        self.protectedATcmd("CMQTTSUB=0," + str(len(self.willSubTopic)) + ",2", lambda: self.printOK(), lambda: self.mqttEnterSubTopic())  # clientIndex = 0

    def mqttEnterSubTopic(self):
        if self.printMessages:
            print("Sub Topic: " + self.willSubTopic)
            self.serialAT.write(self.willSubTopic.encode())

# ----- MQTT Publish ------
    def mqttRequestPublish(self):
        if len(self.txMessage) > 0:
            if self.lteState == LTE_State.MODULE_SHUTTING_DOWN:
                self.shutDownTimerS = 0  # Reset shutdown timer as there is a message to send
            if self.protectedATcmd("CMQTTTOPIC=0," + str(len(self.topic)), lambda: self.mqttRequestPayload(), lambda: self.mqttEnterPubTopic()):  # clientIndex = 0
                return True
            else:
                return False
        else:
            return True

    def mqttEnterPubTopic(self):
        if self.printMessages:
            print("Pub Topic: " + self.topic)
        self.serialAT.write(self.topic.encode())

    def mqttRequestPayload(self):
        self.protectedATcmd("CMQTTPAYLOAD=0," + str(len(self.txMessage)), lambda: self.mqttPublish(), lambda: self.mqttEnterMessage())  # clientIndex = 0

    def mqttEnterMessage(self):
        if self.printMessages:
            print("Publish Message: " + self.topic)
            print(self.txMessage)
        self.serialAT.write(self.txMessage.encode())

    def mqttPublish(self):
        if self.protectedATcmd("CMQTTPUB=0,2,60", lambda: self.printOK(), lambda: None):  # clientIndex = 0
            self.mqttIsPublishing = True  # Block further publishing until publish succeeds or fails.

# --------- GNSS ----------
    def gnssStart(self, interval, oneShot):
        if self.gnssDataCallback is not None:
            self.gnssInterval = interval
            self.gnssOneShot = oneShot
            self.gnssState = GNSS_State.GNSS_REQ_POWERUP

    def powerUpGNSS(self):
        if self.protectedATcmd("CGNSSPWR=1", lambda: self.enableGNSS(), lambda: None):
            self.gnssState = GNSS_State.GNSS_POWERING_UP

    def getGNSSinfo(self):
        if self.gnssState == GNSS_State.GNSS_REQ_DATA:
            self.protectedATcmd("CGNSSINFO", lambda: self.printOK(), lambda: None)

    def powerDownGNSS(self):
        if self.protectedATcmd("CGNSSPWR=0", lambda: self.printOK(), lambda: None):
            self.gnssState = GNSS_State.GNSS_SHUTDOWN

# GNSS Callbacks
    def enableGNSS(self):
        self.protectedATcmd("CGPSHOT", lambda: self.setGNSSready(), lambda: None)

    def setGNSSready(self):
        self.gnssRetryCounter = 0
        self.gnssState = GNSS_State.GNSS_REQ_DATA

    def processGNSSdata(self, nmeaString):
        if len(nmeaString) < 20:  # Make sure it has sensible data
            if self.gnssOneShot:
                self.gnssRetryCounter += 1
                if self.gnssRetryCounter >= 5:  # Only try 5 times
                    self.gnssState = GNSS_State.GNSS_REQ_SHUTDOWN
        else:
            if self.gnssDataCallback is not None:
                self.gnssDataCallback(nmeaString)
                if self.gnssOneShot:
                    self.gnssState = GNSS_State.GNSS_REQ_SHUTDOWN
