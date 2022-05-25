#!/usr/bin/env python3

import pscheduler.batchprocessor
import sys


batch = {
    "schema": 2,

    "#": "Suggested invocation:",
    "#": "pscheduler batch --debug test-input",

    "global": {

        "#": "This is made available to all transforms as $global.",
        "data": {
        "count_multiplier": 1,
            "sponsor": "This measurement is brought to you by perfSONAR.",
            "dest": "ubuntu182"
        },

        "#": "This is applied to all tasks before their task-transform",
        "transform-pre": {
            "script": [
                "  .reference.before = \"This was inserted first.\"",
                "| .reference.sponsor = $global.sponsor",
                "| .reference.iteration = $iteration"
            ]
        },

        "#": "This is applied to all tasks after their task-transform",
        "transform-post": {
            "script": [
                "  .reference.after = \"This was inserted last.\"",

                "# Apply the destination",
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
            "parallel": "true",
            "backoff": "PT1S",
            "sync-start": "true",
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
            "enabled": "true",
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
            "# Replace the test section of the task with one of the",
            "# tests in the reference block based on the iteration.",
            ".test = .reference.tests[$iteration]"
        ]
    }
        }
    ]
}

def debug(message):
    """
    Callback function for the batch processor to emit a line of
    debug.
    """
    print(message, file=sys.stderr)

processor = pscheduler.batchprocessor.BatchProcessor(batch)

# Leave out the debug argument for no debugging.
# This can be invoked multiple times to run the same batch repeatedly.
result = processor(debug=debug)

print(result)
