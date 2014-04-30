import json
import httplib2
import uuid
import base64

class DocuSignClient(object):
	"""
	A client for accessing the DocuSign API.
	"""
	def __init__(self, email, password, integratorKey, demo=False, authBase=None):
		if authBase is None:
			if demo:
				authBase = "https://demo.docusign.net/restapi/v2/login_information"
			else:
				authBase = "https://na2.docusign.net/restapi/v2/login_information"

		self.auth_params = {'email': email, 'password': password, 'integrator_key': integratorKey, 'base': authBase}
		self.authenticated = False

	def authenticate(self):
		self.http = httplib2.Http()
		self.header = "<DocuSignCredentials><Username>%s</Username><Password>%s</Password><IntegratorKey>%s</IntegratorKey></DocuSignCredentials>" % (self.auth_params['email'], self.auth_params['password'], self.auth_params['integrator_key'])
		resp, contentRaw = self.http.request(self.auth_params['base'], "GET", headers={'X-DocuSign-Authentication' : self.header})

		if resp.status != 200:
			return False

		content = json.loads(contentRaw)
		self.accountId = content['loginAccounts'][0]['accountId']
		self.base = str(content['loginAccounts'][0]['baseUrl'])
		self.authenticated = True
		return True

	def createEnvelopeSingle(self, documentName, recipientEmail, recipientName, signX, signY, document):
		if not self.authenticated:
			self.authenticate()

		data = {
			'emailSubject': 'pydocusign - Signature Request on Document',
			'documents': [{'documentId': '1', 'name': documentName}],
			'recipients': {
				'signers': [{
					'email': recipientEmail,
					'name': recipientName,
					'recipientId': '1',
					'tabs': {
						'signHereTabs': [{
							'xPosition': str(signX),
							'yPosition': str(signY),
							'documentId': '1',
							'pageNumber': '1'
						}]
					}
				}]
			},
			'status': 'sent'
		}
		data_json = json.dumps(data)
		boundary = 'myboundary'
		boundaryFull = '--' + boundary

		requestBody = '\r\n'\
			+ '\r\n'\
			+ boundaryFull + '\r\n'\
			+ 'Content-Type: application/json\r\n'\
			+ 'Content-Disposition: form-data\r\n'\
			+ '\r\n'\
			+ data_json + '\r\n'\
			+ boundaryFull + '\r\n'\
			+ 'Content-Type: application/pdf\r\n'\
			+ 'Content-Disposition: file; filename=\"' + documentName + '\"; documentid=1 \r\n'\
			+ '\r\n'\
			+ document + '\r\n'\
			+ boundaryFull + '--\r\n'\
			+ '\r\n'

		resp, contentRaw = self.http.request(self.base + "/envelopes", "POST", body=requestBody, headers={
			'Content-Type': 'multipart/form-data;boundary=' + boundary,
			'Content-Length': str(len(requestBody)),
			'X-DocuSign-Authentication': self.header
		})

		if resp.status != 201:
			print contentRaw
			return False

		content = json.loads(contentRaw)
		return True
