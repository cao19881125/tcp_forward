import api
import info_collection
import json

class ClientConnectionApi(api.RestApiHandler):

    def _get(self,request,response):
        params = self._get_params(request)

        if params.has_key('client_id'):
            worker_id = params['client_id']
        else:
            worker_id = None
        collection = info_collection.InfoCollection.get_instance()

        response.body = json.dumps(collection.get_inner_worker_info(worker_id))

    def _delete(self,request,response):
        params = self._get_params(request)

        try:
            if params.has_key('client_id'):
                info_collection.InfoCollection.get_instance().close_inner_worker(int(params['client_id']))
            elif params.has_key('client_ids'):
                clients_list = json.loads(params['client_ids'])
                for client_id in clients_list:
                    info_collection.InfoCollection.get_instance().close_inner_worker(int(client_id))
        except Exception, e:
            response.body = str({'result': 'failed', 'reason': e.message})
            return

        response.body = json.dumps({'result': 'success'})

    @classmethod
    def factory(cls, global_conf, **kwargs):
        return cls()