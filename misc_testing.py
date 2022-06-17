import pscheduler.batchprocessor
import json

task = {
    "schema": 2,

    "jobs": [

        {
            "label": "wifibssid",
            "task": [{
                "test": {
                    "type": "wifibssid",
                    "spec": {
                        "interface":"wlp0s20f0u11",
                        "ssid":""
                    }
                }}
            ],

        }    
        
    ]
}

processor = pscheduler.batchprocessor.BatchProcessor(task)
result = processor()
print(json.dumps(result))