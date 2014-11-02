import json
from jsonschema import validate, ValidationError, Draft4Validator


def readJSONFile(fileName):
    with open(fileName) as jsonFile:
        data = json.load(jsonFile)
    return data


def validateScripts(instances, schema):
    error = []
    for instance in instances:
        err = validateScript(instance, schema)
        if not err is None:
            error.extend(err)
    if len(error) == 0:
        return None
    else:
        return error


def validateScript(instance, schema):
    try:
        validate(instance, schema)
        return None
    except ValidationError:
        return sorted(Draft4Validator(schema).iter_errors(instance), key=lambda x: x.path)


def generateSchedule(scheduler, scheduleList, callback):
    errors = validateScripts(scheduleList, readJSONFile("script_schema.json"))
    jobs = None
    if errors is None:
        jobs = [scheduler.add_cron_job(callback,
                                       second=med["hour"],
                                       day_of_week=med.get(
                                           "day_of_week", "*"),
                                       args=[med])
                for med in scheduleList]
    else:
        for error in errors:
            print(error)
    return jobs
