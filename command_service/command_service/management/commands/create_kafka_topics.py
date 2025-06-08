# shared/kafka/management/commands/create_kafka_topics.py
from django.core.management.base import BaseCommand
from shared.kafka.topics import Topics, TOPIC_CONFIGS
import logging

logger = logging.getLogger(__name__)

# Check if confluent_kafka is available
try:
    from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource, ResourceType
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("confluent-kafka not installed. Topic creation will be skipped.")
    KAFKA_AVAILABLE = False
    AdminClient = NewTopic = ConfigResource = ResourceType = None

class Command(BaseCommand):
    help = 'Create Kafka topics with configurations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--bootstrap-servers',
            type=str,
            default='kafka:9092',
            help='Kafka bootstrap servers (default: kafka:9092)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating topics'
        )
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing topics before creating new ones'
        )
        parser.add_argument(
            '--topic',
            type=str,
            help='Create only specific topic (optional)'
        )
    
    def handle(self, *args, **options):
        if not KAFKA_AVAILABLE:
            self.stderr.write(
                self.style.ERROR('confluent-kafka not installed. Cannot create topics.')
            )
            return
        
        bootstrap_servers = options['bootstrap_servers']
        dry_run = options['dry_run']
        delete_existing = options['delete_existing']
        specific_topic = options['topic']
        
        self.stdout.write(f"Connecting to Kafka at: {bootstrap_servers}")
        
        # Create admin client
        admin_client = AdminClient({
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'topic-creator'
        })
        
        # Get list of topics to create
        topics_to_create = self.get_topics_to_create(specific_topic)
        
        if dry_run:
            self.show_dry_run(topics_to_create)
            return
        
        # Delete existing topics if requested
        if delete_existing:
            self.delete_existing_topics(admin_client, topics_to_create)
        
        # Create topics
        self.create_topics(admin_client, topics_to_create)
        
        self.stdout.write(
            self.style.SUCCESS('Topic creation completed!')
        )
    
    def get_topics_to_create(self, specific_topic=None):
        """Get list of topics to create from TOPIC_CONFIGS"""
        if specific_topic:
            if specific_topic in TOPIC_CONFIGS:
                return {specific_topic: TOPIC_CONFIGS[specific_topic]}
            else:
                available_topics = ', '.join(TOPIC_CONFIGS.keys())
                self.stderr.write(
                    self.style.ERROR(f'Topic "{specific_topic}" not found in TOPIC_CONFIGS.')
                )
                self.stderr.write(f'Available topics: {available_topics}')
                return {}
        
        return TOPIC_CONFIGS
    
    def show_dry_run(self, topics_to_create):
        """Show what would be created in dry run mode"""
        self.stdout.write(
            self.style.WARNING('DRY RUN MODE - No topics will be created')
        )
        self.stdout.write('')
        
        for topic_name, config in topics_to_create.items():
            self.stdout.write(f"Topic: {topic_name}")
            self.stdout.write(f"  Partitions: {config['partitions']}")
            self.stdout.write(f"  Replication Factor: {config['replication_factor']}")
            self.stdout.write("  Config:")
            for key, value in config['config'].items():
                self.stdout.write(f"    {key}: {value}")
            self.stdout.write("")
    
    def delete_existing_topics(self, admin_client, topics_to_create):
        """Delete existing topics"""
        self.stdout.write("Checking for existing topics to delete...")
        
        # Get existing topics
        metadata = admin_client.list_topics(timeout=10)
        existing_topics = set(metadata.topics.keys())
        
        topics_to_delete = []
        for topic_name in topics_to_create.keys():
            if topic_name in existing_topics:
                topics_to_delete.append(topic_name)
        
        if topics_to_delete:
            self.stdout.write(f"Deleting existing topics: {', '.join(topics_to_delete)}")
            
            delete_result = admin_client.delete_topics(
                topics_to_delete,
                operation_timeout=30
            )
            
            # Wait for deletion to complete
            for topic, future in delete_result.items():
                try:
                    future.result()
                    self.stdout.write(f"  ✓ Deleted topic: {topic}")
                except Exception as e:
                    self.stderr.write(f"  ✗ Failed to delete topic {topic}: {e}")
            
            # Wait a bit for deletion to propagate
            import time
            time.sleep(2)
        else:
            self.stdout.write("No existing topics to delete")
    
    def create_topics(self, admin_client, topics_to_create):
        """Create topics with configurations"""
        self.stdout.write("Creating topics...")
        
        # Prepare NewTopic objects
        new_topics = []
        for topic_name, config in topics_to_create.items():
            new_topic = NewTopic(
                topic=topic_name,
                num_partitions=config['partitions'],
                replication_factor=config['replication_factor'],
                config=config['config']
            )
            new_topics.append(new_topic)
        
        # Create topics
        create_result = admin_client.create_topics(
            new_topics,
            operation_timeout=30
        )
        
        # Wait for creation to complete
        for topic, future in create_result.items():
            try:
                future.result()
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created topic: {topic}")
                )
            except Exception as e:
                if "already exists" in str(e).lower():
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Topic already exists: {topic}")
                    )
                else:
                    self.stderr.write(
                        self.style.ERROR(f"  ✗ Failed to create topic {topic}: {e}")
                    )
        
        # Verify topic configurations
        self.verify_topic_configs(admin_client, topics_to_create)
    
    def verify_topic_configs(self, admin_client, topics_to_create):
        """Verify that topics were created with correct configurations"""
        self.stdout.write("")
        self.stdout.write("Verifying topic configurations...")
        
        # Get topic metadata
        metadata = admin_client.list_topics(timeout=10)
        
        for topic_name, expected_config in topics_to_create.items():
            if topic_name in metadata.topics:
                topic_metadata = metadata.topics[topic_name]
                partition_count = len(topic_metadata.partitions)
                
                self.stdout.write(f"Topic: {topic_name}")
                
                # Check partition count
                if partition_count == expected_config['partitions']:
                    self.stdout.write(f"  ✓ Partitions: {partition_count}")
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Partitions: {partition_count} "
                            f"(expected {expected_config['partitions']})"
                        )
                    )
                
                # Check replication factor
                if topic_metadata.partitions:
                    replication_factor = len(topic_metadata.partitions[0].replicas)
                    if replication_factor == expected_config['replication_factor']:
                        self.stdout.write(f"  ✓ Replication Factor: {replication_factor}")
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Replication Factor: {replication_factor} "
                                f"(expected {expected_config['replication_factor']})"
                            )
                        )
            else:
                self.stderr.write(
                    self.style.ERROR(f"  ✗ Topic not found: {topic_name}")
                )