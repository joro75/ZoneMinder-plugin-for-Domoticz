# ZoneMinder Python Plugin
#
# Author: Frix
# http://zoneminder.readthedocs.io/en/latest/api.html
#
"""
<plugin key="ZoneMinder" name="ZoneMinder" author="Frix" version="1.0" wikilink="http://zoneminder.readthedocs.io/en/stable/api.html">
    <description>
        <h2>ZoneMinder - Monitor Controller</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
			<li>Creates switches for each monitor configured on the ZoneMinder server</li>
			<li>Enables Domoticz to change the status of ZoneMinder monitors</li>
		</ul>
        <h4>Devices</h4>
        <ul style="list-style-type:square">
            <li>State - Selector switch to start/stop/restart ZoneMinder</li>
            <li>Monitor Function - Selector switch to change the Function State of a Monitor. Availible states are "None/Monitor/Modect/Record/Mocord/Nodect".</li>
            <li>Monitor Status - Switch to Disable or Enable the Monitor Function</li>
        </ul>
        <h3>Requirements</h3>
        <ul style="list-style-type:square">
			<li>ZoneMinder API must be enabled, please see the API documentation (Wiki URL) for how to enable the API</li>
			<li>URL Address must contain the complete URL including http:// or https://</li>
        </ul>
    </description>
	<params>
		<param field="Address" label="URL Address" width="250px" required="true" default="http://192.168.1.10/zm"/>
		<param field="Username" label="Username" width="250px" required="false" default="admin"/>
		<param field="Password" label="Password" width="250px" required="false"/>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal"  default="true" />
			</options>
		</param>
	</params>
</plugin>
"""
import Domoticz
import requests
import pyzm
import pyzm.api
import pyzm.ZMEventNotification

class DomoticzLogger:
	'pyzm compatible logger that forwards it to the Domoticz log'
	def __init__(self):
		pass

	def Debug(self, level, message, caller=None):
		Domoticz.Debug('[DEBUG {}] {}'.format(level, message))
		
	def Info(self, message, caller=None):
		Domoticz.Log('[INFO] {}'.format(message))

	def Error(self, message, caller=None):
		Domoticz.Error('[ERROR] {}'.format(message))

	def Fatal(self, message, caller=None):
		Domoticz.Error('[FATAL] {}'.format(message))

	def Panic(self, message, caller=None):
		Domoticz.Error('[PANIC] {}'.format(message))
        
class API:
	def __init__(self):
		self.api = None
		self.ES = None
		self._escallback = None
		return

	def login(self, escallback = None):
		config = {	'apiurl': Parameters["Address"] + '/api', 
				'user': Parameters["Username"], 
				'password': Parameters["Password"],
				'logger': DomoticzLogger()
		}
		self.api = pyzm.api.ZMApi(config)
		if (self.api.authenticated):
			Domoticz.Log("Logged in to " + Parameters["Address"])
		else:
			Domoticz.Log("Failed to authenticate at " + Parameters["Address"])

		self._escallback = escallback
		if self._escallback != None:
			es_config = {
					'url':'ws://192.168.178.108:9000',
					'user': Parameters["Username"],
					'password': Parameters["Password"],
					'on_es_message': lambda msg: self._escallback(msg),
					'logger': DomoticzLogger()
			}
			self.ES = pyzm.ZMEventNotification.ZMEventNotification(es_config)
	def logout(self):
		if self.ES != None:
			self.ES.disconnect()
		
class BasePlugin:
	def __init__(self):
		self.api = API()
		return

	def onStart(self):
		Domoticz.Log("onStart called")
		Domoticz.Heartbeat(30)

		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)

		#Login to ZoneMinder
		self.api.login(lambda msg: self._escallback(msg))

		#Get all existing monitors from ZoneMinder
		monitors = self.api.api.monitors().list()
		mon_count = 0
		if monitors != None:
			mon_count = len(monitors)
		Domoticz.Debug("Number of found monitors: " + str(mon_count))

		#Create Devices for each monitor that was found
		if len(Devices) == 0:
			Options = {"LevelActions": "||||","LevelNames": "Start|Stop|Restart","LevelOffHidden": "True","SelectorStyle": "0"}
			Domoticz.Device(Name="State",  Unit=1, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			Domoticz.Log("Device State with id 1 was created.")

			if (mon_count > 0):
				for monitor in monitors:
					Id = monitor.id()
					Name = monitor.name()
				
					Options = {"LevelActions": "|||||||","LevelNames": "None|Monitor|Modect|Record|Mocord|Nodect","LevelOffHidden": "True","SelectorStyle": "0"}
					Unit = Id * 10 + 1
					Domoticz.Device(Name="Monitor "+ Name +" Function", Unit=Unit, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
					Domoticz.Log("Device Monitor "+ Name +" Function with id "+ str(Unit) +" was created.")
					Unit = Id * 10 + 2
					Domoticz.Device(Name="Monitor "+ Name +" Status", Unit=Unit, Type=17, Switchtype=0).Create()
					Domoticz.Log("Device Monitor "+ Name +" Status with id "+str(Unit)+" was created.")
					Unit = Id * 10 + 3
					Domoticz.Device(Name="Monitor "+ Name +" Alarm", Unit=Unit, Type=17, Switchtype=0).Create()
					Domoticz.Log("Device Monitor "+ Name +" Alarm with id "+str(Unit)+" was created.")


	def onStop(self):
		Domoticz.Log("onStop called")
		self.api.logout()

	def onConnect(self, Connection, Status, Description):
		Domoticz.Log("onConnect called")

	def onMessage(self, Connection, Data):
		Domoticz.Log("onMessage called")

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + Command + "', Level: " + str(Level))
		monitorId = int(Unit / 10)
		function = int(Unit % 10)
		if Unit == 1:
			if Level == 10:
				self.api.api.start()
			if Level == 20:
				self.api.api.stop()
			if Level == 30:
				self.api.api.restart()

		if Unit > 1:
			if function == 1:
				if Level == 0:
					params = {'function' : 'None'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(0))
				if Level == 10:
					params = {'function': 'Monitor'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(10))
				if Level == 20:
					params = {'function':'Modect'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(20))
				if Level == 30:
					params = {'function':'Record'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(30))
				if Level == 40:
					params = {'function':'Mocord'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(40))
				if Level == 50:
					params = {'function':'Nodect'}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(1,str(50))
			if function == 2:
				if Command == "On":
					params = {'enabled': True}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(nValue=1, sValue="On", TimedOut=0)
				if Command == "Off":
					params = { 'raw': {'Monitor[Enabled]': '0' }}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(nValue=0, sValue="Off", TimedOut=0)			
			if function == 3:
				if Command == "On":
					self.api.api.monitors().list()[monitorId - 1].arm()
					Devices[Unit].Update(nValue=1, sValue="On", TimedOut=0)
				if Command == "Off":
					self.api.api.monitors().list()[monitorId - 1].disarm()
					Devices[Unit].Update(nValue=0, sValue="Off", TimedOut=0)			

	def _escallback(self, message):
		Domoticz.Log("ZM ES: Notification: " + str(message))
		if message.get('event') == 'alarm':
			events = message.get('events')
			if events != None:
				for anEvent in events:
					cause = anEvent.get('Cause', '')
					id = anEvent.get('MonitorId', '')
					if len(cause) and len(id):
						alarm = (1, "On")
						if cause[0:4].upper() == 'END:':
							alarm = (0, "Off")
						Devices[int(id) * 10 + 3].Update(nValue=alarm[0], sValue=alarm[1], TimedOut=0)

	def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
		Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

	def onDisconnect(self, Connection):
		Domoticz.Log("onDisconnect called")

	def _isRunning(self):
		url = self.api.api.api_url + '/host/daemonCheck.json'
		result = self.api.api._make_request(url=url)
		return result.get('result', 0) != 0
		
	def onHeartbeat(self):
		Domoticz.Log("onHeartbeat called")
		if self._isRunning():
			Devices[1].Update(1, str(0))
		else:
			Devices[1].Update(0, str(10))
			
		# Check the status of the devices
		# If no devices are found, re-determine if new devices are added
		#	if (len(Devices) == 0):
		#		Domoticz.Debug("No devices found! Retrying to add devices...")
		#		self.onStart()

		#Get an updated status of all existing monitors from ZoneMinder
		options = {'force_reload': True }
		monitors = self.api.api.monitors(options=options).list()
		#Create Devices for each monitor that was found
		if monitors != None and len(monitors) > 0:
			for monitor in monitors:
				Id = monitor.id()
				Name = monitor.name()
				
				selectors = {'None': (1, '0'), 'Monitor': (1, '10'), 'Modect': (1, '20'), 'Record': (1, '30'), 'Mocord': (1, '40'), 'Nodect': (1, '50')}
				function = monitor.function()
				selected = selectors.get(function, None)
				if selected != None:
					Devices[Id * 10 + 1].Update(selected[0], selected[1])
				
				if monitor.enabled():
					Devices[Id * 10 + 2].Update(nValue=1, sValue="On", TimedOut=0)
				else:
					Devices[Id * 10 + 2].Update(nValue=0, sValue="Off", TimedOut=0)

				# Not sure yet how to determine if an alarm is present
				# Domoticz.Device(Name="Monitor "+str(Name)+" Alarm", Unit=int(Id+"3"), Type=17, Switchtype=0).Create()
				# Domoticz.Log("Device Monitor "+str(Name)+" Alarm with id "+str(Id)+"3 was created.")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Data):
    global _plugin
    _plugin.onNotification(Data)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:		   " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:	   '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	" + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return
