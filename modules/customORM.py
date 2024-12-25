import os

import dotenv
import pymongo

from modules import custom_logger

dotenv.load_dotenv()


logger = custom_logger.getLogger('custom_logger')
class CustomORM:
    """
    A custom Object-Relational Mapping (ORM) class for managing MongoDB connections and operations.
    Attributes:
        db (Database): The MongoDB database instance.
        connection_health (bool): The health status of the database connection.
        Initializes the CustomORM instance by establishing a database connection and checking its health.
    """

    def __init__(self):
        self.db = self.get_db_connection()
        self.connection_health = self.check_connection_health()



    def get_db_connection():
        """
        Establish a connection to the MongoDB database.

        Returns:
            Database: The MongoDB database instance.
        """
        root_username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        root_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        client = pymongo.MongoClient(f"mongodb://{root_username}:{root_password}@mongo:27017/")
        return client["HumanFlowTaskManagerDB"]
    
    def check_connection_health(self):
        """
        Check the health of the database connection by sending a ping command.

        Returns:
            bool: True if the ping command was successful, False otherwise.
        """
        try:
            self.db.command("ping")
            logger.info("Successfully connected to MongoDB.")
            return True
        except pymongo.errors.ServerSelectionTimeoutError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
        
    def make_collection_if_not_exists(self, collection_name):
        """
        Create a collection in the database if it does not already exist.
        
        Args:
            collection_name (str): The name of the collection to create.
            
        Returns:
            bool: True if the collection was created, False if it already exists.        
        """
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
            logger.info(f"Collection '{collection_name}' created.")
            return True
        else:
            logger.info(f"Collection '{collection_name}' already exists.")
            return False

    def query_collection(self, collection_name):
        """
        Query a collection in the database.
        
        Args:
            collection_name (str): The name of the collection to query.
            
        Returns:
            list: The documents in the collection.
        """
        documents = list(self.db[collection_name].find())
        logger.info(f"Queried collection '{collection_name}'.")
        return documents

    def insert_one(self, collection_name, document):
        """
        Insert a document into a collection.
        
        Args:
            collection_name (str): The name of the collection.
            document (dict): The document to insert.
            
        Returns:
            bool: True if the document was inserted, False otherwise.
        """
        try:
            self.db[collection_name].insert_one(document)
            logger.info(f"Document inserted into collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to insert document into collection '{collection_name}': {e}")
            return False

    def find_one(self, collection_name, query):
        """
        Find a document in a collection.
        
        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to find the document.
            
        Returns:
            dict: The document if found, None otherwise.
        """
        try:
            document = self.db[collection_name].find_one(query)
            if document:
                logger.info(f"Document found in collection '{collection_name}'.")
            else:
                logger.info(f"Document not found in collection '{collection_name}'.")
            return document
        except Exception as e:
            logger.error(f"Failed to find document in collection '{collection_name}': {e}")
            return None
    
    def find_many(self, collection_name, query):
        """
        Find multiple documents in a collection.
        
        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to find the documents.
            
        Returns:
            list: The documents if found, None otherwise.
        """
        try:
            documents = list(self.db[collection_name].find(query))
            if documents:
                logger.info(f"Documents found in collection '{collection_name}'.")
            else:
                logger.info(f"Documents not found in collection '{collection_name}'.")
            return documents
        except Exception as e:
            logger.error(f"Failed to find documents in collection '{collection_name}': {e}")
            return None

    def update_one(self, collection_name, query, update):
        """
        Update a document in a collection.
        
        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to find the document.
            update (dict): The update to apply to the document.
            
        Returns:
            bool: True if the document was updated, False otherwise.
        """
        try:
            self.db[collection_name].update_one(query, update)
            logger.info(f"Document updated in collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to update document in collection '{collection_name}': {e}")
            return False

    def delete_one(self, collection_name, query):
        """
        Delete a document from a collection.
        
        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to find the document.
            
        Returns:
            bool: True if the document was deleted, False otherwise.
        """
        try:
            self.db[collection_name].delete_one(query)
            logger.info(f"Document deleted from collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document from collection '{collection_name}': {e}")
            return False

    def delete_many(self, collection_name, query):
        """
        Delete multiple documents from a collection.
        
        Args:
            collection_name (str): The name of the collection.
            query (dict): The query to find the documents.
            
        Returns:
            bool: True if the documents were deleted, False otherwise.
        """
        try:
            self.db[collection_name].delete_many(query)
            logger.info(f"Documents deleted from collection '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents from collection '{collection_name}': {e}")
            return False

    def drop_collection(self, collection_name):
        """
        Drop a collection from the database.
        
        Args:
            collection_name (str): The name of the collection to drop.
            
        Returns:
            bool: True if the collection was dropped, False otherwise.
        """
        try:
            self.db[collection_name].drop()
            logger.info(f"Collection '{collection_name}' dropped.")
            return True
        except Exception as e:
            logger.error(f"Failed to drop collection '{collection_name}': {e}")
            return False