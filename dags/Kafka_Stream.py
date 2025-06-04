import uuid
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from confluent_kafka.admin import AdminClient, NewTopic
import logging
default_args = {
    'owner': 'airscholar',
    'start_date': datetime(2023, 9, 3, 10, 00)
}

def create_kafka_topic():
    """Ensure the Kafka topic exists before producing messages."""
    admin_client = AdminClient({'bootstrap.servers':'broker:29092'})
    existing_topics = admin_client.list_topics(timeout=5).topics

    if 'users_created' not in existing_topics:
        logging.info(f"Creating Kafka topic: {'users_created'}")
        topic = NewTopic('users_created', num_partitions=1, replication_factor=1)
        admin_client.create_topics([topic])
    else:
        logging.info(f"Kafka topic {'users_created'} already exists.")

def get_data():
    import requests

    res = requests.get("https://randomuser.me/api/")
    res = res.json()
    res = res['results'][0]

    return res

def format_data(res):
    data = {}
    location = res['location']
    data['id'] = uuid.uuid4()
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data

def stream_data():
    import json
    from kafka import KafkaProducer
    import time
    import logging
    # create_kafka_topic()
    producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=500000)
    curr_time = time.time()

    while True:
        if time.time() > curr_time + 60: #1 minute
            break
        try:
            res = get_data()
            res = format_data(res)
            # print(res)
            res["id"] = str(res["id"])
            producer.send('users_created', json.dumps(res).encode('utf-8')).get(timeout=10)
            producer.flush()
        except Exception as e:
            logging.error(f'An error occured: {e}')
            continue

# create_kafka_topic()
# stream_data()

with DAG('user_automation',
         default_args=default_args,
         schedule='@daily',
         catchup=False) as dag:

    create_topic_task = PythonOperator(
        task_id='create_kafka_topic',
        python_callable=create_kafka_topic
    )
    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data
    )
    create_topic_task >> streaming_task