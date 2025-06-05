import json
import logging
import threading
import time
import uuid
import os
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if confluent_kafka is available
try:
    from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("confluent-kafka not installed. Kafka functionality will be disabled.")
    KAFKA_AVAILABLE = False
    Producer = Consumer = KafkaError = KafkaException = None

class KafkaService:
    """
    Kafka service cho việc gửi và nhận messages
    """
    
    def __init__(self):
        self.producer = None
        self.consumers = {}
        self.kafka_enabled = KAFKA_AVAILABLE and os.getenv('KAFKA_BOOTSTRAP_SERVERS')
        
        if self.kafka_enabled:
            self.kafka_config = {
                'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092'),
                'client.id': os.getenv('KAFKA_CLIENT_ID', 'api-management-service'),
            }
            self._init_producer()
        else:
            logger.info("Kafka is disabled - missing confluent-kafka or KAFKA_BOOTSTRAP_SERVERS")
    
    def _init_producer(self):
        """Initialize Kafka producer"""
        if not self.kafka_enabled:
            return
            
        try:
            producer_config = {
                **self.kafka_config,
                'acks': 'all',
                'retries': 3,
                'retry.backoff.ms': 100,
                'linger.ms': 10,
                'batch.size': 16384,
            }
            self.producer = Producer(producer_config)
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def send_event(self, topic: str, event_type: str, data: Dict[str, Any], 
                   key: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        """
        Gửi event tới Kafka topic
        """
        if not self.kafka_enabled or not self.producer:
            logger.debug(f"Kafka not available, skipping event: {event_type}")
            return False
        
        try:
            # Tạo message payload
            message = {
                'event_id': str(uuid.uuid4()),
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data,
                'source_service': os.getenv('SERVICE_NAME', 'unknown')
            }
            
            # Convert headers to proper format
            kafka_headers = []
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]
            
            # Gửi message
            self.producer.produce(
                topic=topic,
                key=key,
                value=json.dumps(message),
                headers=kafka_headers,
                callback=self._delivery_report
            )
            
            # Flush để đảm bảo message được gửi
            self.producer.flush(timeout=1)
            
            logger.info(f"Event sent to topic {topic}: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to Kafka: {e}")
            return False
    
    def _delivery_report(self, err, msg):
        """Callback cho delivery report"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def create_consumer(self, topics: list, group_id: str, 
                       message_handler: Callable[[Dict[str, Any]], None]):
        """
        Tạo Kafka consumer
        """
        if not self.kafka_enabled:
            logger.warning(f"Kafka not available, cannot create consumer for {group_id}")
            return False
            
        try:
            consumer_config = {
                **self.kafka_config,
                'group.id': group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 1000,
            }
            
            consumer = Consumer(consumer_config)
            consumer.subscribe(topics)
            
            # Store consumer
            self.consumers[group_id] = {
                'consumer': consumer,
                'handler': message_handler,
                'topics': topics,
                'active': True
            }
            
            # Start consumer thread
            thread = threading.Thread(
                target=self._consumer_loop, 
                args=(group_id,),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Consumer created for group {group_id}, topics: {topics}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            return False
    
    def _consumer_loop(self, group_id: str):
        """Consumer loop chạy trong background thread"""
        consumer_info = self.consumers.get(group_id)
        if not consumer_info:
            return
        
        consumer = consumer_info['consumer']
        handler = consumer_info['handler']
        
        try:
            while consumer_info['active']:
                msg = consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition reached {msg.topic()}/{msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                try:
                    # Parse message
                    message_data = json.loads(msg.value().decode('utf-8'))
                    
                    # Call handler
                    handler(message_data)
                    
                    logger.debug(f"Processed message from {msg.topic()}")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KafkaException as e:
            logger.error(f"Kafka consumer error: {e}")
        except Exception as e:
            logger.error(f"Unexpected consumer error: {e}")
        finally:
            try:
                consumer.close()
            except:
                pass
    
    def stop_consumer(self, group_id: str):
        """Stop a specific consumer"""
        if group_id in self.consumers:
            self.consumers[group_id]['active'] = False
            logger.info(f"Stopped consumer {group_id}")
    
    def close(self):
        """Close all connections"""
        # Stop all consumers
        for group_id in self.consumers:
            self.stop_consumer(group_id)
        
        if self.producer:
            self.producer.flush()
        
        logger.info("Kafka service closed")

# Global instance
kafka_service = KafkaService()