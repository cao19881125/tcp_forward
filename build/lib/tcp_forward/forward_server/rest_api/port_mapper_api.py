import api
import info_collection
import json

class PortMapperApi(api.RestApiHandler):
    def _get(self,request,response):
        result =  self.__get_request()
        response.body = result

    def _post(self,request,response):
        #create new port mapper

        params = self._get_params(request)
        if not params.has_key('port') or \
            not params.has_key('mapper_ip') or \
            not params.has_key('mapper_port') or \
            not params.has_key('mapper_tag'):
            response.body = json.dumps({'result':'failed','reason':'parms error'})
            return

        try:


            info_collection.InfoCollection.get_instance().create_new_port(int(params['port']),
                                                                      params['mapper_ip'],
                                                                      int(params['mapper_port']),
                                                                      params['mapper_tag'])
        except Exception,e:
            response.body =json.dumps({'result': 'failed', 'reason': e.message})
            return

        response.body = json.dumps({'result': 'success'})

    def _delete(self,request,response):
        #delete port mapper

        params = self._get_params(request)

        if not params.has_key('port') and not params.has_key('ports'):
            return [json.dumps({'result': 'failed', 'reason': 'parms error'})]

        try:
            if params.has_key('port'):
                info_collection.InfoCollection.get_instance().delete_port(int(params['port']))
            elif params.has_key('ports'):
                ports_list = json.loads(params['ports'])
                for port in ports_list:
                    info_collection.InfoCollection.get_instance().delete_port(int(port))
        except Exception,e:
            response.body = json.dumps({'result': 'failed', 'reason': e.message})
            return
        response.body = json.dumps({'result': 'success'})

    def __get_request(self):
        collection = info_collection.InfoCollection.get_instance()
        return json.dumps(collection.get_port_mapper())


    @classmethod
    def factory(cls,global_conf,**kwargs):
        return cls()

