try:
    import ujson as json
except ModuleNotFoundError:
    import json

#贡献类
class contributions:
    def __init__(self,file_obj):
        self.file_obj = file_obj
        try:
            self.data = json.loads(self.file_obj.read())
        except:
            self.data = {"groups": {}}
            self.write_data()

    def update_data(self,time_when_update,data,ubi_name,group_id = 0,member_id = 0):
        if not group_id in self.data["groups"]:
            self.data["groups"]["group_id"] = {}
        if not member_id in self.data["groups"][group_id]:
            self.data["groups"]["group_id"][member_id] = []           
            self.data["groups"]["group_id"][member_id].append(time_when_update,ubi_name,data)

    def write_data(self):
        self.file_obj.write(json.dumps(self.data))