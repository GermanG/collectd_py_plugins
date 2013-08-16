import json
import urllib2, base64
import collectd

RABBIT_HOST = 'localhost'
RABBIT_PORT = 15672
RABBIT_USER = 'guest'
RABBIT_PASS = 'guest'

def configure(config):
	global RABBIT_HOST, RABBIT_PORT, RABBIT_USER, RABBIT_PASS
	collectd.info('Configuring Stuff')
        for node in config.children:
		if node.key == 'Host':
			RABBIT_HOST =  node.values[0]
		elif node.key == 'Port':
			RABBIT_PORT =  int(node.values[0])
		elif node.key == 'User':
			RABBIT_USER =  node.values[0]
		elif node.key == 'Password':
			RABBIT_PASS =  node.values[0]
		else:
			collectd.warning('rabbitmq_collectd plugin: Unknown config key: %s.' % node.key) 

def dispatch_value(info, key, type, plugin_instance=None, type_instance=None):
	"""Read a key from info response data and dispatch a value"""
	if not isinstance(info, dict):
#		collectd.warning('rabbitmq_collectd plugin: Info key not found: %s' % key)
		return
	elif key not in info:
#		collectd.warning('rabbitmq_collectd plugin: Info key not found: %s' % key)
		return

	if not type_instance:
		type_instance = key

	value = int(info[key])

	# log_verbose('Sending value: %s=%s' % (type_instance, value))
	# collectd.info('Sending value: %s %s %s=%s' % (key, plugin_instance, type_instance, value))

	val = collectd.Values(plugin='rabbitmq.%s.%s' % (plugin_instance,type_instance))
	val.type = type
	val.values = [value]

	val.dispatch()

def read():
	global RABBIT_HOST, RABBIT_PORT, RABBIT_USER, RABBIT_PASS
	request = urllib2.Request('http://%s:%s/api/queues' % (RABBIT_HOST, RABBIT_PORT))
	base64string = base64.encodestring('%s:%s' % (RABBIT_USER, RABBIT_PASS)).replace('\n', '')
	request.add_header("Authorization", "Basic %s" % base64string)   
	result = urllib2.urlopen(request)

	if not result:
		collectd.error('rabbitmq plugin: No info received')
		return

	jason = json.loads(result.read())

	for queue in jason:
		plugin_instance  = queue['vhost']
		type_instance = queue['name']
                if plugin_instance == '/':
			plugin_instance = 'root'
		dispatch_value(queue, 'messages', 'messages', plugin_instance, type_instance)
		if 'messages_details' in queue:
			dispatch_value(queue['messages_details'], 'rate', 'messages_rate', plugin_instance, type_instance)
		dispatch_value(queue, 'messages_unacknowledged', 'messages_unacknowledged', plugin_instance, type_instance)
		if 'messages_unacknowledged_details' in queue:
			dispatch_value(queue['messages_unacknowledged_details'], 'rate', 'messages_unacknowledged_rate', plugin_instance, type_instance)
		dispatch_value(queue, 'messages_ready', 'messages_ready', plugin_instance, type_instance)
		if 'messages_ready' in queue:
			dispatch_value(queue['messages_ready'], 'rate', 'messages_ready_rate', plugin_instance, type_instance)
		dispatch_value(queue, 'memory', 'mq_memory', plugin_instance, type_instance)
		dispatch_value(queue, 'consumers', 'consumers', plugin_instance, type_instance)
		if 'message_stats' in queue: 
			dispatch_value(queue['message_stats'], 'publish', 'publish', plugin_instance, type_instance)
			if 'publish_details' in queue['message_stats']: 
				dispatch_value(queue['message_stats']['publish_details'], 'rate', 'publish_rate', plugin_instance, type_instance)
			dispatch_value(queue['message_stats'],'deliver_no_ack', 'deliver_no_ack', plugin_instance, type_instance)
			if 'deliver_no_ack_details' in queue['message_stats']: 
				dispatch_value(queue['message_stats']['deliver_no_ack_details'], 'rate', 'deliver_no_ack_rate', plugin_instance, type_instance)
			dispatch_value(queue['message_stats'],'deliver_get', 'deliver_get', plugin_instance, type_instance)
			if 'deliver_get_details' in queue['message_stats']: 
				dispatch_value(queue['message_stats']['deliver_get_details'], 'rate', 'deliver_get_rate', plugin_instance, type_instance)

def shutdown():
        collectd.info('python plugin shutting down')


collectd.register_config(configure)
collectd.register_read(read)
collectd.register_shutdown(shutdown)
