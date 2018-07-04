import api
import info_collection

class ClientConnectionApi(api.RestApiHandler):

    def _get(self,request):
        params = self._get_params(request)

        if params.has_key('client_id'):
            worker_id = params['client_id']
        else:
            worker_id = None
        collection = info_collection.InfoCollection.get_instance()

        return [str(collection.get_inner_worker_info(worker_id))]

    def _delete(self,request):
        params = self._get_params(request)

        try:
            if params.has_key('client_id'):
                info_collection.InfoCollection.get_instance().close_inner_worker(int(params['client_id']))
        except Exception, e:
            return [str({'result': 'failed', 'reason': e.message})]

        return [str({'result': 'success'})]

    @classmethod
    def factory(cls, global_conf, **kwargs):
        return cls()