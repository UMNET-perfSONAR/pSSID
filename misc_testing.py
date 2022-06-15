import pscheduler.batchprocessor

task = {
    "schema": 2,

    "jobs": [

        {
            "label": "wifibssid",
            "task": [{
                "test": {
                    "type": "wifibssid",
                    "spec": {
                        "interface":"wlp0s20f0u11" 
                    }
                }}
            ],

        }    
        
    ]
}

processor = pscheduler.batchprocessor.BatchProcessor(task)
result = processor(True)
print(result)