import json
import logging
import threading
import time
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from django.conf import settings

logger = logging.getLogger(__name__)

class KafkaService:
    """
    Kafka service cho việc gửi và nhận messages
    """
    
    def __init__(self):
        self.producer = None
        self.consumers = {}
        self.kafka_config = {
            'bootstrap.servers': getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092'),
            'client.id': getattr(settings, 'KAFKA_CLIENT_ID', 'api-management-service'),
        }
        self._init_producer()
    
    def _init_producer(self):
        """Initialize Kafka producer"""
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
        
        Args:
            topic: Kafka topic name
            event_type: Loại event (command_executed, user_action, etc.)
            data: Event data
            key: Message key (optional)
            headers: Message headers (optional)
        """
        if not self.producer:
            logger.warning("Kafka producer not available, skipping event")
            return False
        
        try:
            # Tạo message payload
            message = {
                'event_id': str(uuid.uuid4()),
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'data': data,
                'source_service': getattr(settings, 'SERVICE_NAME', 'unknown')
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
        
        Args:
            topics: List of topics to subscribe
            group_id: Consumer group ID
            message_handler: Function to handle received messages
        """
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
                'topics': topics
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
            while True:
                msg = consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()}/{msg.partition()}")
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
        finally:
            consumer.close()
    
    def close(self):
        """Close all connections"""
        if self.producer:
            self.producer.flush()
        
        for group_id, consumer_info in self.consumers.items():
            consumer_info['consumer'].close()
        
        logger.info("Kafka service closed")

kafka_service = KafkaService()

class EventTypes:
    # User events
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_REGISTERED = 'user_registered'
    
    # Vendor events
    VENDOR_CREATED = 'vendor_created'
    VENDOR_UPDATED = 'vendor_updated'
    VENDOR_ACTIVATED = 'vendor_activated'
    VENDOR_DEACTIVATED = 'vendor_deactivated'
    
    # API Configuration events
    API_CONFIG_CREATED = 'api_config_created'
    API_CONFIG_UPDATED = 'api_config_updated'
    API_CONFIG_TESTED = 'api_config_tested'
    
    # Command execution events
    COMMAND_REQUESTED = 'command_requested'
    COMMAND_EXECUTED = 'command_executed'
    COMMAND_FAILED = 'command_failed'
    
    # System events
    SYSTEM_ERROR = 'system_error'
    SYSTEM_WARNING = 'system_warning'

class Topics:
    USER_EVENTS = 'user-events'
    VENDOR_EVENTS = 'vendor-events'
    API_CONFIG_EVENTS = 'api-config-events'
    COMMAND_EVENTS = 'command-events'
    SYSTEM_EVENTS = 'system-events'
    AUDIT_EVENTS = 'audit-events'