from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URL)
        print("Connected to MongoDB")

    def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_master_db(self):
        return self.client[settings.MONGO_DB_NAME]

    def get_org_db_name(self, org_name: str) -> str:
        return f"org_{org_name}"

    def get_org_collection(self, org_name: str):
        # In this design, each org has its own COLLECTION or DB?
        # Requirement: "Dynamically create a new Mongo collection specifically for the organization. Example collection name pattern: org_<organization_name>."
        # It says "new Mongo collection", so likely in the SAME database (Master DB? or a specific App DB?)
        # "Store the following in the Master Database: Organization name... Connection details (if required)".
        # Use Master DB for metadata.
        # Use Dynamic Collections in the SAME Master DB? Or separate DBs?
        # "Dynamically create a new Mongo collection... create dynamic collections for each organization."
        # Typically "multi-tenant style architecture" often implies separate DBs or separate collections.
        # Given "Example collection name pattern: org_<organization_name>", it implies separate collections in the SAME DB.
        # Let's stick to collections in the same DB for simplicity unless "Connection details" implies separate servers.
        # "Connection details (if required)" -> hints at separate DBs/Servers being possible.
        # But for this assignment, collections in `master_db` or a separate `tenants_db` is fine.
        # I'll put them in `master_db` for now or maybe better `tenants_db` to keep metadata clean?
        # Requirement: "The system should maintain a Master Database for global metadata and create dynamic collections for each organization."
        # Use `master_db` for metadata.
        # The dynamic collections can live in `master_db` too for simplicity, or I can treat `master_db` as purely metadata.
        # I'll put them in `master_db` to avoid complexity, or `settings.MONGO_DB_NAME`.
        return self.client[settings.MONGO_DB_NAME][self.get_org_db_name(org_name)]

db = MongoDB()
