from django.shortcuts import render
from django.views.generic import TemplateView
from collections import OrderedDict
import json
import requests
####SMART HOME API STUFF#####

#So my password for my account is not on github...
PassDoc = open("../../password.txt", 'r') #change back after testing
Password = PassDoc.read()

#KASA HOME STUFF##
def GetToken():
	param = OrderedDict([("appType", "Kasa_Android"), ("cloudUserName","gmsiders@gmail.com"),("cloudPassword", Password),("terminalUUID","c55f1c98-f486-4a69-8ce6-adb9ce6f0eea")])
	data = json.dumps(OrderedDict([("method", "login") , ("params", param)]))
	r = requests.post('https://wap.tplinkcloud.com', data=data)
	token_data = json.loads(r.text)
	token = token_data['result']['token']
	return token
	
def GetKasaDeviceStatus(token,id):
	params = OrderedDict([("deviceId", id), ("requestData", "{\"system\":{\"get_sysinfo\":{}}}")])
	data = json.dumps(OrderedDict([("method", "passthrough") , ("params", params)]))
	param = {"token" : token } 
	r = requests.post('https://use1-wap.tplinkcloud.com/', params=param, data=data)
	device_status = json.loads(r.text)
	status = json.loads(device_status['result']['responseData'])['system']['get_sysinfo']['relay_state']
	if status == 1:
		return "on"
	if status == 0:
		return "off"

def GetKasaDeviceList(token):
	data = { "method" : "getDeviceList" }
	param = {"token" : token }
	r = requests.post('https://wap.tplinkcloud.com', params=param, data=json.dumps(data))
	device_list = json.loads(r.text)
	devices = []
	for i in device_list['result']['deviceList']:
		alias = i['alias']
		id = i['deviceId']
		devices.append([alias,id])
	return devices
			
def TurnOnSmartPlug(token,id):
	params = OrderedDict([("deviceId", id), ("requestData", "{\"system\":{\"set_relay_state\":{\"state\":1}}}" )])
	data = json.dumps(OrderedDict([("method", "passthrough") , ("params", params)]))
	param = {"token" : token }
	r = requests.post('https://use1-wap.tplinkcloud.com/', params=param, data=data)
	print(r.text)

def TurnOffSmartPlug(token,id):
	params = OrderedDict([("deviceId", id), ("requestData", "{\"system\":{\"set_relay_state\":{\"state\":0}}}" )])
	data = json.dumps(OrderedDict([("method", "passthrough") , ("params", params)]))
	param = {"token" : token }
	r = requests.post('https://use1-wap.tplinkcloud.com/', params=param, data=data)
	print(r.text)

##HUE STUFF##

#GET X-TOKEN using AUTH TOKEN FROM HUE USERS ACCOUNT

def GetHueToken():
	s = requests.Session()
	s.get('https://my.meethue.com/en-us/?token=ca11b7e83e8cb6b83bea8f1482168faf7ed92aaf123f753f899b3ec99b3409cb291b97d961a419be07c9ace1e77069e076841297c7bf0a9e7f81904e54581cbe')
	cookies = s.cookies.get_dict()
	token = cookies['myhueapi']
	return token

#SETS HEADERS FOR REQUEST OBJECT AND GETS TOKEN 
def GetHeaders():
	token = GetHueToken()
	headers = OrderedDict([("x-token",token),("content-type","application/json")])
	return headers

#RETURNS UNFORMATED JSON OBJECT OF STATUS OF ALL LIGHTS
def GetStatus(header):
	header = header
	r = requests.get("https://client.meethue.com/api/0", headers=header)
	return r.text
	
#GETS LIGHT BULB STATUS OF SPECIFIC BULB
def GetBulbStatus(status, bulbid):
	status = json.loads(status)
	id = bulbid
	state = status['lights'][id]['state']['on']
	if state == True:
		print("Light is on")
	if state == False:
		print("Light is off")

#DATA TYPES ARE IMPORTANT
#>>> json1 = {"on":'true',"bri":'114'}
#>>> json2 = {"on":True,"bri":114}
#>>> j.dumps(json1)
#'{"on": "true", "bri": "114"}'
#>>> j.dumps(json2)
#'{"on": true, "bri": 114}'

#Turns specific light off
def TurnHueLightOff(header, bulbid):
	header = header
	id = bulbid
	data = {"on":False}
	data = json.dumps(data)
	url = "https://client.meethue.com/api/0/lights/%i/state" % id 
	r = requests.put(url,headers=header,data=data)
	result = json.loads(r.text)
	error = 'error' in result[0]
	if error == True:
		result = "Error: Couldn't turn light off"
	if error == False:
		result = "Light succesfully turned on."
	return result
	

#Turns specific light on
def TurnHueLightOn(header, bulbid):
	header = header
	id = bulbid
	data = {"on":True}
	data = json.dumps(data)
	url = "https://client.meethue.com/api/0/lights/%i/state" % id 
	r = requests.put(url,headers=header,data=data)
	result = json.loads(r.text)
	error = 'error' in result[0]
	if error == True:
		result = True
	if error == False:
		result = False
	return result
	
#Gets all hue lights status 
def GetAllHueStatus(header):
	status = GetStatus(header)
	status = json.loads(status)
	lights = status['lights']
	AllLightStates = []
	for light in lights:
		id = light
		name = status['lights'][id]['name']
		state = status['lights'][id]['state']['on']
		if state == False:
			state = "off"
		if state == True:
			state = "on"
		bri = status['lights'][id]['state']['bri']
		AllLightStates.append([id,name,state,bri])
	return AllLightStates

#Set brightness on specific hue light 
def SetHueBrightness(header, bulbid, level):
	id = bulbid
	data = {"bri": level}
	data = json.dumps(data)
	url = "https://client.meethue.com/api/0/lights/%i/state" % id
	r = requests.put(url,headers=header,data=data)
	result = json.loads(r.text)
	error = 'error' in result[0]
	if error == True:
		result = "Error: Light is either off or unreachable."
	if error == False:
		result = "Light brightness succesfully changed."
	return result

#Begin Django View###


class LightStatus:
	def __init__(self,id):
		self.id = id
		self.name = None
		self.state = None
		self.bri = None
	def add_data(self,id,name,state,bri):
		self.id = id
		self.name = name
		self.state = state
		self.bri = bri

def HomePageStrings():
	token = GetToken()
	devices = GetKasaDeviceList(token)
	KasaData = OrderedDict([('token', token), ('devices', devices)])
	HueHeader = GetHeaders()
	HueData = GetAllHueStatus(HueHeader)
	HueData = HueData
	data = []
	data.append([KasaData])
	data.append([HueData])
	return data
	

def dashboard(request):
	data = HomePageStrings()
	token = data[0][0]['token']
	id1 = data[0][0]['devices'][0][1]
	id2 = data[0][0]['devices'][1][1]
	name1 = data[0][0]['devices'][0][0]
	name2 = data[0][0]['devices'][1][0]
	AllLights = dict()
	print(data[1])
	for i in data[1]:
		for light in i:
			id = light[0]
			name = light[1]
			state = light[2]
			bri = light[3]
			AllLights[id] = LightStatus(id)
			AllLights[id].add_data(id,name,state,bri)
	status1 = GetKasaDeviceStatus(token, id1)
	status2 = GetKasaDeviceStatus(token, id2)
	return render(request, 'index.html', {'id1': id1, 'status1': status1, 'name1': name1,'id2': id2, 'status2': status2, 'name2': name2,'lights': AllLights})
	
def turnonhue(request):
	id = request.GET.get('id')
	HueHeader = GetHeaders()
	id = int(id)
	print(type(id))
	TurnHueLightOn(HueHeader, id)
	#will turn all the shit below this into a function later...so I don't have to declare it everytime...i'm lazy
	data = HomePageStrings()
	token = data[0][0]['token']
	id1 = data[0][0]['devices'][0][1]
	id2 = data[0][0]['devices'][1][1]
	name1 = data[0][0]['devices'][0][0]
	name2 = data[0][0]['devices'][1][0]
	AllLights = dict()
	print(data[1])
	for i in data[1]:
		for light in i:
			id = light[0]
			name = light[1]
			state = light[2]
			bri = light[3]
			AllLights[id] = LightStatus(id)
			AllLights[id].add_data(id,name,state,bri)
	status1 = GetKasaDeviceStatus(token, id1)
	status2 = GetKasaDeviceStatus(token, id2)
	return render(request, 'index.html', {'id1': id1, 'status1': status1, 'name1': name1,'id2': id2, 'status2': status2, 'name2': name2,'lights': AllLights})
def turnoffhue(request):
	id = request.GET.get('id')
	HueHeader = GetHeaders()
	id = int(id)
	print(type(id))
	TurnHueLightOff(HueHeader, id)
	#will turn all the shit below this into a function later...so I don't have to declare it everytime...i'm lazy
	data = HomePageStrings()
	token = data[0][0]['token']
	id1 = data[0][0]['devices'][0][1]
	id2 = data[0][0]['devices'][1][1]
	name1 = data[0][0]['devices'][0][0]
	name2 = data[0][0]['devices'][1][0]
	AllLights = dict()
	print(data[1])
	for i in data[1]:
		for light in i:
			id = light[0]
			name = light[1]
			state = light[2]
			bri = light[3]
			AllLights[id] = LightStatus(id)
			AllLights[id].add_data(id,name,state,bri)
	status1 = GetKasaDeviceStatus(token, id1)
	status2 = GetKasaDeviceStatus(token, id2)
	return render(request, 'index.html', {'id1': id1, 'status1': status1, 'name1': name1,'id2': id2, 'status2': status2, 'name2': name2,'lights': AllLights})
	
def turnoff(request):
	token = GetToken()
	id = request.GET.get('id')
	TurnOffSmartPlug(token,id)
	data = HomePageStrings()
	token = data[0][0]['token']
	id1 = data[0][0]['devices'][0][1]
	id2 = data[0][0]['devices'][1][1]
	name1 = data[0][0]['devices'][0][0]
	name2 = data[0][0]['devices'][1][0]
	status1 = GetKasaDeviceStatus(token, id1)
	status2 = GetKasaDeviceStatus(token, id2)
	return render(request, 'index.html', {'id1': id1, 'status1': status1, 'name1': name1,'id2': id2, 'status2': status2, 'name2': name2})
	
def turnon(request):
	token = GetToken()
	id = request.GET.get('id')
	TurnOnSmartPlug(token,id)
	data = HomePageStrings()
	token = data[0][0]['token']
	id1 = data[0][0]['devices'][0][1]
	id2 = data[0][0]['devices'][1][1]
	name1 = data[0][0]['devices'][0][0]
	name2 = data[0][0]['devices'][1][0]
	status1 = GetKasaDeviceStatus(token, id1)
	status2 = GetKasaDeviceStatus(token, id2)
	return render(request, 'index.html', {'id1': id1, 'status1': status1, 'name1': name1,'id2': id2, 'status2': status2, 'name2': name2})
	