
from __future__ import annotations
import serial
import time
import logging
from enum import Enum
from .schedular import Schedular

logger = logging.getLogger(__name__)


#  TODO In the serial init add AT+CGMM and throw an exception if you don't get a response or the correct response.
#  TODO don't setup LWT unless will topic and message is setup. Remove offlineMessage


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
    SHUTDOWN_WAIT_S = 10

    onOKCallback = None
    onEnterCallback = None

    imei = ""  # Use imei as the client ID for MQTT

    onReceiveIncomingMessageCallback = None
    onMQTTconnectCallback = None
    onMQTTsubscribeCallback = None
    onMQTTpublishCallback = None

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
    mqttReconnectFailCounter = 0
    disconnectTimerS = 0
    runATcallbacks = False

    lteState = LTE_State.MODULE_STARTUP
    errorState = ERROR_State.ERR_REBOOT
    mqttState = MQTT_State.MQTT_DISCONNECTED

    willTopic = ""
    willMessage = ""
    mqttIsPublishing = False
    pubTopic = ""
    subTopic = ""
    mqttIsSubscribing = False
    messageSendID = -1
    lastCommand = ""  # ??? is this being used anymore
    messagesDict = {}

    username = ""
    password = ""

    gnssDataCallback = None
    gnssInterval = 60
    gnssOneShot = False
    gnssIntervalTimerS = 0
    gnssRetryCounter = 0
    gnssState = GNSS_State.GNSS_SHUTDOWN

    def __init__(self, _serial, _network, _apn, _baud_rate):
        self.network = _network
        self.apn = _apn
        self.serialAT = serial.Serial(_serial, _baud_rate)
        self.serialAT.flush()
        sched = Schedular("LTE Connection Schedular")
        sched.add_timer(1.0, 0.0, self.run)
        sched.add_timer(1.0, 0.25, self.runOneSecondModuleTasks)
        sched.add_timer(1.0, 0.5, self.runOneSecondMQTTTasks)
        sched.add_timer(1.0, 0.75, self.runOneSecondGNSSTasks)

    def mqttSetup(self,  _host, _port, _username, _password):
        self.username = _username
        self.password = _password
        self.host = _host
        self.port = _port

    def setCallbacks(self, _onMQTTconnect, _onMQTTsubscribe, _receiveIncomingMessage):
        self.onMQTTconnectCallback = _onMQTTconnect
        self.onMQTTsubscribeCallback = _onMQTTsubscribe
        self.onReceiveIncomingMessageCallback = _receiveIncomingMessage

    def subscribe(self, _topic):
        self.subTopic = _topic

    def publishMessage(self, topic, message):
        if topic not in self.messagesDict.keys():
            self.messagesDict[topic] = message
        else:
            self.messagesDict[topic] += message

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
        self.mqttIsSubscribing = False
        self.mqttState = MQTT_State.MQTT_DISCONNECTED
        self.gnssState = GNSS_State.GNSS_OFF

    def onMQTTconnected(self):
        self.mqttState = MQTT_State.MQTT_CONNECTED

        if self.onMQTTconnectCallback is not None:
            self.onMQTTconnectCallback(True, self.errorState)

        self.errorState = ERROR_State.ERR_NONE

    def run(self, cookie):
        self.processATcommands()

        # Messaging
        if (self.mqttState == MQTT_State.MQTT_CONNECTED) and (not self.runATcallbacks):
            if not self.mqttIsSubscribing and not self.mqttIsPublishing and not self.incomingMessage:  # Wait for any received message being downloaded.
                if len(self.subTopic) > 0:
                    self.mqttReqSubscribe()
                elif len(self.messagesDict) > 0:
                    dTopic = list(self.messagesDict.keys())[0]
                    self.mqttRequestPublish(dTopic, self.messagesDict[dTopic])

        return True

    def processATcommands(self):
        if self.serialAT.in_waiting > 0:
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
                    logger.debug("CMD: %s", data)

                    if data.startswith("OK"):
                        logger.debug('\n')

                        if self.runATcallbacks:
                            self.runATcallbacks = False
                            if (self.onOKCallback is not None):
                                self.onOKCallback()
                    elif (data.startswith("ERROR")):
                        self.moreDataComing = 0  # Just in case
                        if (self.runATcallbacks):
                            self.runATcallbacks = False
                            logger.debug("Callback - Houston - we have a problem ERROR")
                            logger.debug("AT Error")
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
                                logger.debug("ME PDN ACT")
                            elif (resultStr.startswith("EPS PDN ACT")):  # AcT = 7 (EUTRAN)
                                logger.debug("EPS PDN ACT")
                            elif (resultStr.startswith("ME PDN DEACT")):
                                logger.debug("ME PDN DEACT")
                            elif (resultStr.startswith("NW PDN DEACT")):
                                logger.debug("NW PDN DEACT")
                        elif data.startswith("+SIMEI:"):
                            self.imei = "IMEI" + resultStr
                        elif data.startswith("+COPS:"):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 3:
                                logger.debug("Carrier: %s", resultArr[2])
                        # MQTT
                        elif (data.startswith("+CMQTTSTART:")):
                            error = int(resultStr)
                            if (error == 0):
                                self.mqttAcquireCLient()
                            else:
                                logger.debug("MQTT Start: %s", error)
                                self.lteState = LTE_State.MODULE_REQ_RESET
                        elif (data.startswith("+CMQTTCONNECT:")):
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if (error == 0):
                                    self.onMQTTconnected()
                                    self.mqttReconnectFailCounter = 0
                                else:
                                    logger.debug("MQTT Cnct: %s", error)
                                    self.reqMQTTreconnect()
                        elif data.startswith("+CMQTTSUB:"):
                            self.mqttIsSubscribing = False
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if self.onMQTTsubscribeCallback is not None:
                                    self.onMQTTsubscribeCallback(self.subTopic, error)

                                if error == 0:
                                    self.subTopic = ""
                                else:
                                    logger.debug("MQTT Sub: %s", error)
                                    self.reqMQTTreconnect()
                        elif data.startswith("+CMQTTPUB:"):
                            self.mqttIsPublishing = False
                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                if error == 0:
                                    if self.pubTopic in self.messagesDict:
                                        del self.messagesDict[self.pubTopic]  # ??? This should really be after successful publish
                                else:
                                    logger.debug("MQTT Pub: %s", error)
                                    self.reqMQTTreconnect()

                                if self.onMQTTpublishCallback is not None:
                                    self.onMQTTpublishCallback(self.pubTopic, self.messageSendID, error)  # Do before topic is cleared below
                                self.messageSendID = -1  # Probably don't need this

                                self.pubTopic = ""
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
                                if self.onReceiveIncomingMessageCallback is not None:
                                    self.onReceiveIncomingMessageCallback(self.rxMessage)
                                self.rxMessage = ""
                        elif data.startswith("+CMQTTDISC:"):
                            self.mqttState = MQTT_State.MQTT_DISCONNECTED
                            if self.shutDownTimerS >= 0:
                                self.lteState = LTE_State.MODULE_REQ_SHUTDOWN
                        elif data.startswith("+CMQTTCONNLOST:"):
                            self.mqttState = MQTT_State.MQTT_DISCONNECTED
                            if self.onMQTTconnectCallback is not None:
                                self.onMQTTconnectCallback(False, ERROR_State.ERR_MQTT_CONNECTION_LOST)

                            resultArr = resultStr.split(',')
                            if len(resultArr) >= 2:
                                error = int(resultArr[1])
                                logger.debug("MQTT Cnct Lost: %s", error)
                                self.reqMQTTreconnect()
                        # GNSS
                        elif data.startswith("+CGNSSINFO:"):
                            self.processGNSSdata(resultStr)

    def readMessage(self, messageLen):
        charsIn = self.serialAT.read().decode()
        self.rxMessage += charsIn
        self.moreDataComing = messageLen - len(charsIn)

    def runOneSecondModuleTasks(self, cookie):
        if self.shutDownTimerS >= 0:
            logger.debug("Shutdown Ttimers: %ss", self.shutDownTimerS)
            self.shutDownTimerS += 1
            if (self.shutDownTimerS == self.SHUTDOWN_WAIT_S):
                self.mqttState = MQTT_State.MQTT_REQ_DISCONNECT
            if (self.shutDownTimerS == self.SHUTDOWN_WAIT_S + 5):  # Allow 5 seconds to disconnect before shutdown
                self.shutDownTimerS = -1  # Turn off timer
                self.lteState = LTE_State.MODULE_REQ_SHUTDOWN

        # LTE State
        if self.lteState == LTE_State.MODULE_STARTUP:
            logger.debug("Disconnect Timers: %s.", self.disconnectTimerS)
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
            logger.debug("Disconnect Timers: %s^", self.disconnectTimerS)
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
                    logger.debug("Callback - Houston - we have a problem TIMEOUT")
                    self.timeoutErrorCommand = self.lastCommand
                    self.reqResetModule(ERROR_State.ERR_AT_TIMEOUT_RESET)
        return True

    def runOneSecondMQTTTasks(self, cookie):
        if self.mqttState == MQTT_State.MQTT_REQ_CONNECT:
            self.mqttConnect()
        elif self.mqttState == MQTT_State.MQTT_REQ_DISCONNECT:
            self.mqttDisconnect()

        if self.mqttReconnectTimerS >= 0:
            self.mqttReconnectTimerS += 1
            logger.debug("mqttReconnectTimers: %sm.", self.mqttReconnectTimerS)
            if self.mqttReconnectTimerS >= 10:
                self.mqttReconnectTimerS = -1  # Turn off timer
                logger.debug("MQTT Reconnect")
                self.reqMQTTconnect()
        return True

    def runOneSecondGNSSTasks(self, cookie):
        if self.gnssState == GNSS_State.GNSS_REQ_POWERUP:
            self.powerUpGNSS()
        elif self.gnssState == GNSS_State.GNSS_REQ_DATA:
            self.gnssIntervalTimerS += 1
            logger.debug("gnssIntervalTimerS: %s", self.gnssIntervalTimerS)
            if self.gnssIntervalTimerS >= self.gnssInterval:
                self.gnssIntervalTimerS = 0
                self.getGNSSinfo()
        elif self.gnssState == GNSS_State.GNSS_REQ_SHUTDOWN:
            self.powerDownGNSS()
        return True

    def powerDownModule(self):
        self.lteState = LTE_State.MODULE_SHUTTING_DOWN
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
        logger.debug("OK ACK")

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
        tempStr += self.imei  # cliendID
        tempStr += "\",1"  # serverType 1 = SSL/TLS, 0 = TCP
        self.protectedATcmd(tempStr, lambda: self.mqttConfigSSL(), lambda: None)

    def mqttConfigSSL(self):
        self.protectedATcmd("CMQTTSSLCFG=0,0", lambda: self.mqttRequestWillToic(), lambda: None)  # sessionID = 0, sslIndex = 0

# ---- MQTT LWT -----
    def mqttRequestWillToic(self):
        if len(self.willMessage) > 0 and len(self.willTopic) > 0:
            self.protectedATcmd("CMQTTWILLTOPIC=0," + str(len(self.willTopic)), lambda: self.mqttRequestWillMessage(), lambda: self.mqttEnterWillToic())  # clientIndex = 0
        else:
            self.mqttConnect()

    def mqttEnterWillToic(self):
        self.serialAT.write((self.willTopic).encode())

    def mqttRequestWillMessage(self):
        tempStr = "CMQTTWILLMSG=0,"
        tempStr += str(len(self.willMessage))
        tempStr += ",2"
        self.protectedATcmd(tempStr, lambda: self.reqMQTTconnect(), lambda: self.mqttEnterWillMessage())  # clientIndex = 0, qos = 2

    def mqttEnterWillMessage(self):
        self.serialAT.write(self.willMessage.encode())

    def reqMQTTconnect(self):
        self.mqttState = MQTT_State.MQTT_REQ_CONNECT

# ---- MQTT Connect -----
    def mqttConnect(self):
        connectStr = "CMQTTCONNECT=0,\"tcp://"
        connectStr += self.host
        connectStr += ":"
        connectStr += str(self.port)
        connectStr += "\",60,1,\""  # 60s keep alive
        connectStr += self.username
        connectStr += "\",\""
        connectStr += self.password
        connectStr += "\""
        if self.protectedATcmd(connectStr, lambda: self.printOK(), lambda: None, 60):  # Allow 60s for MQTT to connect
            self.mqttState = MQTT_State.MQTT_CONNECTING

# ---- MQTT Subscribe -----
    def mqttReqSubscribe(self):
        if self.protectedATcmd("CMQTTSUB=0," + str(len(self.subTopic)) + ",2", lambda: self.printOK(), lambda: self.mqttEnterSubTopic()):  # clientIndex = 0
            self.mqttIsSubscribing = True

    def mqttEnterSubTopic(self):
        logger.debug("Sub Topic: %s", self.subTopic)
        self.serialAT.write(self.subTopic.encode())

# ----- MQTT Publish ------
    def mqttRequestPublish(self, topic, message):
        self.pubTopic = topic
        self.txMessage = message
        if len(self.txMessage) > 0:
            if self.lteState == LTE_State.MODULE_SHUTTING_DOWN:
                self.shutDownTimerS = 0  # Reset shutdown timer as there is a message to send
            if self.protectedATcmd("CMQTTTOPIC=0," + str(len(self.pubTopic)), lambda: self.mqttRequestPayload(), lambda: self.mqttEnterPubTopic()):  # clientIndex = 0
                return True
            else:
                return False
        else:
            return True

    def mqttEnterPubTopic(self):
        logger.debug("Pub Topic: %s", self.pubTopic)
        self.serialAT.write(self.pubTopic.encode())

    def mqttRequestPayload(self):
        self.protectedATcmd("CMQTTPAYLOAD=0," + str(len(self.txMessage)), lambda: self.mqttPublish(), lambda: self.mqttEnterMessage())  # clientIndex = 0

    def mqttEnterMessage(self):
        logger.debug("Publish Message: %s\n%s", self.pubTopic, self.txMessage)
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
