"""
Check archive configurations
"""

import argparse
import json


parser = argparse.ArgumentParser(
	description='Validating the archiver fields')
parser.add_argument(
	'config_file', action='store', help='config.json')
parser.add_argument(
	'ref_file', action='store', help='archivers_refs.json')
args = parser.parse_args()


def check(config_archive, archiver_name):
	"""Validates each defined archiver."""	
	try:
		required = archivers_refs[archiver_name]['required']
		all_keys = required + archivers_refs[archiver_name]['optional']
	except KeyError:
		print("'{}' is not a valid archiver name".format(archiver_name))
		exit(1)

	for each_key in required:
		if each_key not in config_archive['data'].keys():
			print("'{}' archiver must include '{}' key"
				.format(archiver_name, each_key))
			exit(1)
	
	for each_key in config_archive['data'].keys():
		if each_key not in all_keys:
			print("'{}' archiver includes invalid key '{}'"
				.format(archiver_name, each_key))
			exit(1)


config = json.loads(open(args.config_file, 'r').read())
archivers_refs = json.loads(open(args.ref_file, 'r').read())

# Checks if archives is defined in config file
if 'archives' not in config:
	exit(0)

archivers = config['archives']

for archive in archivers.values():
	check(archive, archive['archiver'])
