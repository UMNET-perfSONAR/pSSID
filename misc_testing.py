import pscheduler.batchprocessor

task = {
    "schema": 2,

    "jobs": [

        {
            "label": "wifibssid",
            "task": [{
                "test": {
                    "type": "http",
                    "spec": {
                       "url": "http://google.com"
                    }
                }}
            ],

        }    
        
    ]
}

processor = pscheduler.batchprocessor.BatchProcessor(task)
result = processor()
print(result)