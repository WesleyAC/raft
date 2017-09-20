class Client:
	def __init__(self, client_id, conf, rng, broker):
		self.client_id = client_id
		self.conf = conf
		self.rng = rng
		self.broker = broker


	def receive(self, sender, message):
		pass

	def send_message(self, data):
		pass
