import json
import pscheduler.batchprocessor

def __init__(self, parsed_file):
    self.p = parsed_file
    self.s = sched.scheduler(time.time, time.sleep)
    self.jobs = []


def run_batch_process():

    for tests in parsed_file.active_batches:
        
        job_instance = {
                "label": tests,
                "parallel": True,
                "task": []
            }
        for job in jobs: 
            test_instance = {
                "test": parsed_file.tests[job]
            }
            job_instance["task"].append(test_instance) 
        
        batch_temp["jobs"].append(job_instance)


    json_str = json.dumps(self)
    
    print(json_str)
    processor = pscheduler.batchprocessor.BatchProcessor(batch_temp)

    # Leave out the debug argument for no debugging.
    # This can be invoked multiple times to run the same batch repeatedly.
    result = processor(debug=debug)
