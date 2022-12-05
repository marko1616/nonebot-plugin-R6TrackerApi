import time
try:
    import ujson as json
except ModuleNotFoundError:
    import json

#贡献类
class contributions:
    def __init__(self,file_path):
        self.file_path = file_path
        with open(self.file_path,"r") as file_obj:
            try:
                self.data = json.loads(file_obj.read())
            except:
                self.data = {"basic":{},"days":{}}
                self.write_data()

    def update_data(self,time_when_update,data,ubi_name):
        if str(time_when_update) not in self.data["basic"]:
            self.data["basic"][str(time_when_update)] = []
        self.data["basic"][str(time_when_update)].append((ubi_name,data))
        self.write_data()

    def read_data(self):
        return self.data

    def write_data(self):
        with open(self.file_path,"w+") as file_obj:
            file_obj.write(json.dumps(self.data))
    
    def get_data_today(self):
        sorted_key = sorted(self.data["basic"],reverse=True)
        time_newest = float(sorted_key[0])
        newest_data = self.data["basic"][sorted_key[0]]
        today_num_data = []
        for tmp_time in sorted_key:
            today_first_data = self.data["basic"][tmp_time]
            if time.strftime("%d",time.localtime(float(tmp_time))) != time.strftime("%d",time.localtime(time_newest)):
                break
        ubi_name_have = [data[0] for data in today_first_data]
        for ubi_name,num in newest_data:
            if ubi_name in ubi_name_have:
                today_num = num - today_first_data[ubi_name_have.index(ubi_name)][1]
                today_num_data.append((ubi_name,today_num))
        return today_num_data
    
    def get_ones_year_data(self,ubi_name):
        res = [0]*365
        year = time.strftime('%Y',time.localtime())
        for data in self.data["days"]:
            data_time = time.mktime(time.strptime(data,"%a %b %d %H:%M:%S %Y"))
            if time.strftime('%Y',time.localtime(data_time)) == year:
                for user in self.data["days"][data]:
                    if user[0] == ubi_name:
                        res[int(time.strftime('%j',time.localtime(data_time)))-1] = user[1]
        return res
    
    def write_today_data(self):
        self.data["days"][time.asctime(time.localtime())] = self.get_data_today()
        self.data["basic"] = {}
        self.write_data()