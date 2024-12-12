import time 
#Get timestamp as string, in format DDMMYY_hhmm
def get_timestamp() -> str:
    time_struct = time.localtime(time.time())
    stamp = str(time_struct.tm_mday) + str(time_struct.tm_mon) + str(time_struct.tm_year)[2:] + "_" + str(time_struct.tm_hour) + str(time_struct.tm_min)
    return stamp
# Print time taken (in seconds) to sucessfully compute the given function call
def performance_decorator(function):
    def wrapper(*args, **kwargs):
        timestamp = time.time()
        result = function(*args, **kwargs)
        print(f"{function.__name__} completed in {round(time.time() - timestamp, 4)}s")
        return result
    
    return wrapper