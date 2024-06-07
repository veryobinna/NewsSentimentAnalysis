from kafka.consumer import KafkaConsumer

brokers = "localhost:9092"
topic = "big-data-project"

consumer = KafkaConsumer(topic, bootstrap_servers=brokers)

title = ["source", "total_trump_mentions","positive", "negative", "total"]
print(*title, sep=", ")

for msg in consumer:
    if msg.value:
        data = msg.value.decode('utf-8').split(",")
        print(*data, sep=", ")

        