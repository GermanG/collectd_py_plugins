import base64
import collectd
import re
import os

# This is a php-fpm memory usage plugin for collect
# but made it having in mind to extend it to other processes/regex

PROCESS_NAME_REGEX = '^php-fpm:'
PROCESS_NAME = 'php-fpm'

def configure(config):
	global PROCESS_NAME_REGEX
	collectd.info('Configuring Stuff')
        for node in config.children:
		if node.key == 'ProcessRegex':
			PROCESS_NAME_REGEX =  node.values[0]
		elif node.key == 'ProcessName':
			PROCESS_NAME =  node.values[0]
		else:
			collectd.warning('memory_usage plugin: Unknown config key: %s.' % node.key) 

def memory_used(process_re):
	pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

	memory = 0
	for pid in pids:
		try:
			a = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
			fpm_re = re.search(process_re, a) # look for php-fpm
			if fpm_re:
				# print "%s %s" % (pid, a) # just debugging
				for line in open(os.path.join('/proc', pid, 'status')): #greplike pythonese
					if "VmRSS" in line:
						memory += int(re.sub(' +', ' ',line).split(" ")[1])
		except IOError: # proc has already terminated
			continue

	return [ memory * 1024 ]
	

def read():
	global PROCESS_NAME_REGEX, PROCESS_NAME
	metric = collectd.Values();
	metric.plugin = 'memory_usage.%s' % PROCESS_NAME
	metric.type = 'gauge'
	metric.values = memory_used(PROCESS_NAME_REGEX)
        # collectd.info('memory usage plugin %s %s' % (metric.plugin,metric.values) )
	metric.dispatch()


def shutdown():
        collectd.info('python plugin shutting down')


collectd.register_config(configure)
collectd.register_read(read)
collectd.register_shutdown(shutdown)
