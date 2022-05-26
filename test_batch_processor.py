#!/usr/bin/env python3
from parse_config import Parse, tests
import argparse
import pscheduler.batchprocessor
import sys
import json
batch = r"""{
    "schema": 2,
    "global": {
        "data": {
        "count_multiplier": 1,
            "sponsor": "This measurement is brought to you by perfSONAR.",
            "dest": "ubuntu182"
        },
        "transform-pre": {
            "script": [
                "  .reference.before = \"This was inserted first.\"",
                "| .reference.sponsor = $global.sponsor",
                "| .reference.iteration = $iteration"
            ]
        },
        "transform-post": {
            "script": [
                "  .reference.after = \"This was inserted last.\"",

                "| if (.test.spec | has(\"dest\"))",
                "    then .test.spec.dest = $global.dest",
                "    else . end"
            ]
        }
    },
    "jobs": [

        {

            "label": "noop",
            "iterations": 1,
            "parallel": true,
            "backoff": "PT1S",
            "sync-start": true,
            "task": {
                "test": {
                    "type": "noop",
                    "spec": {
                        "fail":0 
                    }
                }
            },
         "continue-if": {
                "script": ".[0].runs[0].\"application/json\".succeeded"
        }
        },

        {
            "label": "tasks",
            "iterations": 3,
            "enabled": true,
            "task": {
                        "reference":{
                                "tests":[
                                        {                   
                                                "type": "rtt",
                                                "spec": {
                                                "dest": "ubuntu182"
                                                }
                                        },
                                        {
                                                "type": "throughput",
                                                "spec": {
                                                        "dest": "ubuntu182",
                                                        "duration": "PT1M"
                                                }
                                        },
                                        {
                                                "type": "trace",
                                                "spec": {
                                                "schema": 1,
                                                "dest": "ubuntu182"
                                                }

                                        }
                                ]
                        },
                        "test": {}
            },
         "continue-if": {
                "script": ".[0].runs[0].\"application/json\".succeeded"
        },
            "task-transform": {
        "script": [
            ".test = .reference.tests[$iteration]"
        ]
    }
        }
    ]
}"""



def debug(message):
    """
    Callback function for the batch processor to emit a line of
    debug.
    """
    print(message, file=sys.stderr)

parser = argparse.ArgumentParser(description='pSSID')
parser.add_argument('file', action='store',
  help='json file')
parser.add_argument('--debug', action='store_true',
  help='sanity check')
args = parser.parse_args()

# read config file
# call function in parse_config.py
# parse_config.py sub-main will validate that the config file is correct
config_file = open(args.file, "r")
parsed_file = Parse(config_file)
config_file.close()


batch_temp = {
                        "schema": 2,
                        "global": {
                            "data": {
                            "count_multiplier": 1,
                                "dest": "ubuntu182"
                            },
                            "transform-pre": {
                                "script": [
                                    "  .reference.before = \"This was inserted first.\"",
                                    "| .reference.sponsor = $global.sponsor",
                                    "| .reference.iteration = $iteration"
                                ]
                            },
                            "transform-post": {
                                "script": [
                                    "  .reference.after = \"This was inserted last.\"",

                                    "| if (.test.spec | has(\"dest\"))",
                                    "    then .test.spec.dest = $global.dest",
                                    "    else . end"
                                ]
                            }
                        },
                        "jobs": []
                    }

for tests in parsed_file.active_batches:
    
    job_instance = {
            "label": tests,
            "parallel": True,
            "task": []
        }
    for job in parsed_file.batches[tests]["jobs"]: 
        test_instance = {
            "test": parsed_file.tests[job]
        }
        job_instance["task"].append(test_instance) 
    
    batch_temp["jobs"].append(job_instance)


json_str = json.dumps(batch_temp)

print(json_str)
processor = pscheduler.batchprocessor.BatchProcessor(batch_temp)

# Leave out the debug argument for no debugging.
# This can be invoked multiple times to run the same batch repeatedly.
result = processor(debug=debug)

#print(actual_batch)
