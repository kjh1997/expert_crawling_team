from kafka import KafkaConsumer 
from json import loads # topic, broker list 
consumer_byte = KafkaConsumer("test",
                              bootstrap_servers="127.0.0.1:9092", 
                              group_id = None,
                              enable_auto_commit=True,
                              auto_offset_reset='earliest',
                              consumer_timeout_ms = 5000
                             )
try : 
    for msg in consumer_byte :
        print(msg.value.decode("unicode_escape"))
        print(msg.topic, msg.partition, msg.offset, msg.key)
        print("")
    
except :

    print("finished --- 1")
