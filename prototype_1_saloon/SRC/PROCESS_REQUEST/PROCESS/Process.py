from .HelperFunctions import extract_phn_number, get_mapped_fields, read_record
from .STORAGE_MANAGEMENT.Online_transaction.StoredData.CLIENT.ManageClient import writeout_data
from .CLIENT_MANAGEMENT.Client import load_record, validate_fields, merge_record, update_system_fields
from .SharedData import response_queue

class manage_customer_appoinment:
    def __init__(self):
        self.session_key = None
        self.res = ""
        return

    def manage_res(self, val):
        return self.res

    def book_apinment(self):
        return self.manage_res(self.res)
    
    def cancel_appoinment(self):
        return self.manage_res(self.res)
    
    def postphone_appoinment(self):
        return self.manage_res(self.res)
    
    def store_data(self):
        return self.manage_res(self.res)
    
class manage_client_data:
    def __init__(self, keys, current_action, RequestData):
        self.session_key = keys["sessionKey"]
        self.seq_key = keys["seqId"]
        self.current_action = current_action
        self.client_schema = 'PROCESS\CLIENT_MANAGEMENT'
        self.stored_data = "PROCESS\STORAGE_MANAGEMENT\Online_transaction\StoredData\CLIENT\StoreData"
        self.stored_history_data = "PROCESS\STORAGE_MANAGEMENT\Online_transaction\StoredData\CLIENT\history_data"
        self.res = ""
        self.thread_name = None
        self.phone_number = None
        response_queue["{}#{}".format(self.seq_key, self.session_key)] = []
        self.test_mode = True
        self.request_data = RequestData
        return
    
    def manage_res(self, val):
        response_queue["{}#{}".format(self.seq_key, self.session_key)].append(self.res)
        return self.res

    def create_client(self, RequestData, thread_name = None):
        self.thread_name = thread_name
        self.phone_number = extract_phn_number(RequestData)
        RequestData, old_session_number = update_system_fields(RequestData, self.session_key, self.seq_key)
        self.res = writeout_data(self.seq_key, self.session_key, self.phone_number, self.request_data, self.test_mode, self.current_action, old_session_number)
        return self.manage_res(self.res)
    
    def delete_client(self, RequestData):
        return self.manage_res(self.res)
    
    def update_client(self, RequestData, thread_name=None):

        self.thread_name = thread_name
        self.phone_number = extract_phn_number(RequestData)

        #validate new record
        schema_file = read_record("create_schema")
        all_keys = get_mapped_fields(schema_file)
        missing_fields = validate_fields(RequestData, all_keys)

        #load current record
        current_record = load_record("CURRENT", self.phone_number)

        #load new record
        combined_paths = {}
        new_record = load_record("CURRENT", self.phone_number, request_data=RequestData, current_data=current_record, combined_paths=all_keys)

        #move current record to history data

        #delete current data

        #move new record to current data
        
        return self.manage_res(self.res)
    
    def store_data(self):
        return self.manage_res(self.res)
    
