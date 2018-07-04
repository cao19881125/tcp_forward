## 获取客户端连接端口
#### Request
请求 | url
---|---
GET | /client_port

#### Response

```
{
    "client_port:"1111
}
```

## 获取端口映射
#### Request
请求 | url
---|---
GET | /port_mapper
#### Resopnse

```
{
1234:{"ip":127.0.0.1,"port":3456,"tag":"default"},
4321:{"ip":192.168.1.10,"port":8080,"tag":"client-one"}
}
```
## 创建端口映射
#### Request
请求 | url
---|---
POST | /port_mapper?port=55&mapper_ip=192.168.10.15&mapper_port=6666&mapper_tag=tag10

#### Resopnse
- 成功
```
{
    "result":"success"
}
```
- 失败

```
{
    "result":"failed",
    "reason":"xxx"
}
```
### 例子：

```
# curl -X POST "http://127.0.0.1:8080/port_mapper?port=5433&mapper_ip=192.168.10.15&mapper_port=6666&mapper_tag=tag10"
{'result': 'success'}
```


```
# curl -X POST "http://127.0.0.1:8080/port_mapper?port=5433&mapper_ip=192.168.10.15&mapper_port=6666&mapper_tag=tag10"
{'reason': 'Create port mapper failed,port:5433 already exists', 'result': 'failed'}
```



## 删除端口映射
#### Request
请求 | url
---|---
DELETE | /port_mapper?port=55

#### Resopnse
- 成功
```
{
    "result":"success"
}
```
- 失败

```
{
    "result":"failed",
    "reason":"xxx"
}
```

### 例子：
```
# curl -X DELETE "http://127.0.0.1:8080/port_mapper?port=5555"
{'result': 'success'}
```


## 获取客户端连接状态
#### Request
- 获取所有连接状态

请求 | url
---|---
GET | /client_connection

- 获取固定客户端连接状态

请求 | url
---|---
GET | /client_connection?client_id=123

#### Resopnse

```
{
    12:{
    "init_time":"2018-07-03 14:04:00",
    "duration_time":65463,
    "ip":127.0.0.1,
    "port":3456,
    "tag":"default",
    "state":"WORKING",
    "recv_flow_statistics":100,
    "recv_real_time_speed":"10",
    "recv_average_speed":1,
    "send_flow_statistics":100,
    "send_real_time_speed":"10",
    "send_average_speed":1,    
    }
}
```
- duration_time：持续时间单位是秒
- flow_statistics：流量统计单位是M
- real_time_speed: 实时速度单位MB/s
- average_speed : 平均速度单位MB/s

### 举例

```
# curl http://127.0.0.1:8080/client_connection
{1: {'client_ip': '127.0.0.1', 'state': 'WORKING', 'duration_time': 24, 'init_time': '2018-7-3 16:44:41', 'recv_average_speed': 1.664033493166159e-05, 'send_flow_statistics': 4226.250317573547, 'client_port': 38790, 'send_real_time_speed': 0, 'recv_flow_statistics': 0.0004062652587890625, 'send_average_speed': 173.10419551768555, 'client_tag': 'default', 'recv_real_time_speed': 0}}
```
## 强制关闭某客户端
请求 | url
---|---
DELETE | /client_connection?client_id=123


#### Resopnse
- 成功
```
{
    "result":"success"
}
```
- 失败

```
{
    "result":"failed",
    "reason":"xxx"
}
```

## 获取当前通道列表
#### Request
- 获取所有端口通道

请求 | url
---|---
GET | /channel

- 获取指定端口通道

请求 | url
---|---
GET | /channel?port=1234

#### Resopnse

```
{
    1234:[
        {
            "channel_id":5,
            "ip":"102.32.44.11",
            "port":3421,
            "state":"WORKING"
        },
        {
            "channel_id":6,
            "ip":"102.32.44.11",
            "port":3421,
            "state":"WORKING"
        }
    ]
}
```
### 举例

```
# curl http://127.0.0.1:8080/channel
{5555: [{'channel_id': 2, 'state': 'WORKING', 'port': 57984, 'ip': '192.168.184.1'}, {'channel_id': 3, 'state': 'WORKING', 'port': 58002, 'ip': '192.168.184.1'}]}
```


```
# curl http://127.0.0.1:8080/channel?port=5555
{5555: [{'channel_id': 2, 'state': 'WORKING', 'port': 57984, 'ip': '192.168.184.1'}]}
```



## 获取通道详细信息
#### Request
请求 | url
---|---
GET | /channel?channel_id=12

#### Resopnse

```
{
    12:{
    "init_time":"2018-07-03 14:04:00",
    "duration_time":65463,
    "ip":127.0.0.1,
    "port":3456,
    "state":"WORKING",
    "recv_flow_statistics":100,
    "recv_real_time_speed":"10",
    "recv_average_speed":1,
    "send_flow_statistics":100,
    "send_real_time_speed":"10",
    "send_average_speed":1,    
    }
}
```
### 举例

```
# curl http://127.0.0.1:8080/channel?channel_id=2
{2: {'ip': '192.168.184.1', 'state': 'WORKING', 'duration_time': 8, 'init_time': '2018-7-4 10:12:38', 'send_flow_statistics': 0.010096549987792969, 'recv_real_time_speed': 0, 'recv_average_speed': 0.00044058766769542487, 'send_real_time_speed': 0, 'recv_flow_statistics': 0.0035486221313476562, 'send_average_speed': 0.0012535612738015461, 'port': 59550}}
```


## 强制关闭某通道
#### Request
请求 | url
---|---
DELETE | /channel?channel_id=12

#### Resopnse
- 成功
```
{
    "result":"success"
}
```
- 失败

```
{
    "result":"failed",
    "reason":"xxx"
}
```



## 获取通道历史记录
