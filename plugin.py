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

class API:
	def __init__(self):
		self.api = None
		return

	def login(self):
		config = {	'apiurl': Parameters["Address"] + '/api', 
				'user': Parameters["Username"], 
				'password': Parameters["Password"]
		}
		self.api = pyzm.api.ZMApi(config)
		if (self.api.authenticated):
			Domoticz.Log("Logged in to " + Parameters["Address"])
		else:
			Domoticz.Log("Failed to authenticate at " + Parameters["Address"])

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
		self.api.login()

		#Get all existing monitors from ZoneMinder
		monitors = self.api.api.monitors().list()
		Domoticz.Debug("Number of found monitors: " + str(len(monitors)))

		#Create Devices for each monitor that was found
		if len(Devices) == 0:
			if (len(monitors) > 0):
				Options = {"LevelActions": "||||","LevelNames": "Start|Stop|Restart","LevelOffHidden": "True","SelectorStyle": "0"}
				Domoticz.Device(Name="State",  Unit=1, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
				Domoticz.Log("Device State with id 1 was created.")

				for monitor in monitors:
					Id = str(monitor.id())
					Name = monitor.name()
				
					Options = {"LevelActions": "|||||||","LevelNames": "None|Monitor|Modect|Record|Mocord|Nodect","LevelOffHidden": "True","SelectorStyle": "0"}
					Domoticz.Device(Name="Monitor "+str(Name)+" Function",  Unit=int(Id+"1"), TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
					Domoticz.Log("Device Monitor "+str(Name)+" Function with id "+str(Id)+"1 was created.")
					Domoticz.Device(Name="Monitor "+str(Name)+" Status", Unit=int(Id+"2"), Type=17, Switchtype=0).Create()
					Domoticz.Log("Device Monitor "+str(Name)+" Status with id "+str(Id)+"2 was created.")
					Domoticz.Device(Name="Monitor "+str(Name)+" Alarm", Unit=int(Id+"3"), Type=17, Switchtype=0).Create()
					Domoticz.Log("Device Monitor "+str(Name)+" Alarm with id "+str(Id)+"3 was created.")


	def onStop(self):
		Domoticz.Log("onStop called")

	def onConnect(self, Connection, Status, Description):
		Domoticz.Log("onConnect called")

	def onMessage(self, Connection, Data):
		Domoticz.Log("onMessage called")

	def onCommand(self, Unit, Command, Level, Hue):
		Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
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
					params = {'enabled': False}
					self.api.api.monitors().list()[monitorId - 1].set_parameter(params)
					Devices[Unit].Update(nValue=0, sValue="Off", TimedOut=0)			
			if function == 3:
				if Command == "On":
					self.api.api.monitors().list()[monitorId - 1].arm()
					Devices[Unit].Update(nValue=1, sValue="On", TimedOut=0)
				if Command == "Off":
					self.api.api.monitors().list()[monitorId - 1].disarm()
					Devices[Unit].Update(nValue=0, sValue="Off", TimedOut=0)			

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
