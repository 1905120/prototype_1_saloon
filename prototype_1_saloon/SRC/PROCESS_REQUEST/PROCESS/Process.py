from .HelperFunctions import get_mapped_fields, read_record
from .STORAGE_MANAGEMENT.Online_transaction.StoredData.CLIENT.ManageClient import writeout_data, delete_data
from .CLIENT_MANAGEMENT.Client import load_record, validate_fields, update_system_fields, current_sys_fields
from . import SharedData
import copy

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
        self.phone_number = keys["phoneNumber"]
        self.err_key = keys["errKey"]
        self.current_action = current_action
        self.client_schema = 'PROCESS\CLIENT_MANAGEMENT'
        self.stored_data = "PROCESS\STORAGE_MANAGEMENT\Online_transaction\StoredData\CLIENT\StoreData"
        self.stored_history_data = "PROCESS\STORAGE_MANAGEMENT\Online_transaction\StoredData\CLIENT\history_data"
        self.res = ""
        self.thread_name = None
        self.test_mode = True
        self.request_data = RequestData
        return
    
    def manage_res(self, val):
        return self.seq_key, self.session_key, self.phone_number, self.res

    def create_client(self, RequestData, thread_name = None):
        self.thread_name = thread_name
        RequestData["barber_shop"]["versionNo"] = 0
        RequestData["barber_shop"]["id"] = self.seq_key
        RequestData = update_system_fields(RequestData, None, self.session_key)
        self.res = writeout_data(self.seq_key, self.session_key, self.phone_number, self.request_data, self.current_action)
        return self.manage_res(self.res)
    
    def delete_client(self, RequestData):
        return self.manage_res(self.res)
    
    def update_client(self, RequestData, thread_name=None):

        self.thread_name = thread_name

        #validate new record
        schema_file = read_record("create_schema")
        all_keys = get_mapped_fields(schema_file)
        missing_fields = validate_fields(RequestData, all_keys["fields"])

        #load current record
        client_seq_id, session_id = current_sys_fields(self.phone_number, SharedData.client_meta_data)
        old_record, err_msg       = load_record("CURRENT", self.phone_number, client_seq_id, session_id)

        #move current record to history data
        move_res = writeout_data(client_seq_id, session_id, self.phone_number, old_record, self.current_action)
        
        #load new record
        new_record, err_msg      = load_record("NEW", self.phone_number, None, None, RequestData, old_record, all_keys)
        #update sysfields for new record
        new_record               = update_system_fields(new_record, session_id, self.session_key)

        

        #delete current data
        del_res = delete_data(client_seq_id, session_id, self.phone_number)

        #move new record to current data
        self.res = writeout_data(client_seq_id, self.session_key, self.phone_number, new_record, "CREATE-CLIENT")

        return self.manage_res(self.res)
    
    def store_data(self):
        return self.manage_res(self.res)
    
