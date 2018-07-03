import api
import info_collection

class PortMapperApi(api.RestApiHandler):

    def _get(self,request):
        return self.__get_request()

    def _post(self,request):
        #create new port mapper
        
        return []

    @classmethod
    def factory(cls,global_conf,**kwargs):
        return cls()

    def __get_request(self):
        collection = info_collection.InfoCollection.get_instance()
        return [collection.get_port_mapper_str()]