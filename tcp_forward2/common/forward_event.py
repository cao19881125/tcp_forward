
FDEVENT = 'FDEvent'
TRANSDATAEVENT = 'TransDataEvent'
CLOSECONEVENT = 'CloseConEvent'
SCHEDULEREVENT = 'SchedulerEvent'

class ForwardEvent(object):
    def __init__(self,event_type):
        self.event_type = event_type

class FDEvent(ForwardEvent):
    def __init__(self,fd_event):
        super(FDEvent,self).__init__(FDEVENT)
        self.fd_event = fd_event

class SchedulerEvent(ForwardEvent):
    def __init__(self):
        super(SchedulerEvent,self).__init__(SCHEDULEREVENT)

class TransDataEvent(ForwardEvent):
    def __init__(self,forward_id,forward_data):
        super(TransDataEvent,self).__init__(TRANSDATAEVENT)
        self.forward_id = forward_id
        self.forward_data = forward_data

class CloseConEvent(ForwardEvent):
    def __init__(self,forward_id):
        super(CloseConEvent,self).__init__(CLOSECONEVENT)
        self.forward_id = forward_id


def event_filter(func):
    def filter(*args,**kwargs):
        if type(args[1]) == int:
            f_event = FDEvent(args[1])
        else:
            f_event = args[1]

        if not isinstance(f_event,ForwardEvent):
            raise Exception('event_filter event is not subclass of ForwardEvent:' + str(type(f_event)))

        func(args[0],f_event,*args[2:],**kwargs)
    return filter