import api
import info_collection

class ChannelApi(api.RestApiHandler):
    def _get(self, request,response):
        params = self._get_params(request)

        if len(params) == 0:
            #get all port info
            result = self._get_port_info(None)
        elif params.has_key('port'):
            #get specified port info
            result = self._get_port_info(int(params['port']))
        elif params.has_key('channel_id'):
            #get specified channel info
            result = self._get_channel_info(int(params['channel_id']))
        response.body = result

    def _get_port_info(self,port = None):
        result = info_collection.InfoCollection.get_instance().get_channel_info_by_port(port)

        return str(result)

    def _get_channel_info(self,channel_id):
        collection = info_collection.InfoCollection.get_instance()
        return str(collection.get_outer_worker_info(channel_id))

    def _delete(self,request,response):
        params = self._get_params(request)

        try:
            if params.has_key('channel_id'):
                info_collection.InfoCollection.get_instance().close_outer_worker(int(params['channel_id']))
        except Exception, e:
            return [str({'result': 'failed', 'reason': e.message})]

        response.body = str({'result': 'success'})


    @classmethod
    def factory(cls, global_conf, **kwargs):
        return cls()