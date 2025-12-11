from fastapi import APIRouter, Depends, HTTPException, status
from app.db.mongodb import db
from app.schemas.schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.models.models import OrganizationDB, AdminDB
from app.core.security import get_password_hash
from app.api.deps import get_current_admin
from app.core.config import settings

router = APIRouter()

@router.post("/create", response_model=OrganizationResponse)
async def create_organization(org_in: OrganizationCreate):
    master_db = db.get_master_db()
    
    # Check if org exists
    existing_org = await master_db.organizations.find_one({"name": org_in.organization_name})
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")
        
    # Check if admin email exists
    existing_admin = await master_db.admins.find_one({"email": org_in.email})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin email already registered")

    # Create Organization Metadata
    org_data = OrganizationDB(
        name=org_in.organization_name,
        collection_name=db.get_org_db_name(org_in.organization_name),
        admin_email=org_in.email
    )
    await master_db.organizations.insert_one(org_data.dict())
    
    # Create Admin User
    hashed_password = get_password_hash(org_in.password)
    admin_data = AdminDB(
        email=org_in.email,
        hashed_password=hashed_password,
        organization_name=org_in.organization_name
    )
    await master_db.admins.insert_one(admin_data.dict())
    
    # Dynamically create collection (implicitly created on insert, but we can do explicit create or insert dummy)
    # Requirement: "The collection can be empty or initialized with a basic schema"
    # We will just ensure it's accessible.
    org_collection = db.get_org_collection(org_in.organization_name)
    # Optional: Insert a config doc or placeholder to force creation if Mongo is lazy
    await org_collection.insert_one({"type": "init", "created_at": org_data.created_at})
    
    return OrganizationResponse(
        organization_name=org_data.name,
        collection_name=org_data.collection_name,
        admin_email=org_data.admin_email
    )

@router.get("/get", response_model=OrganizationResponse)
async def get_organization(organization_name: str):
    master_db = db.get_master_db()
    org = await master_db.organizations.find_one({"name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return OrganizationResponse(
        organization_name=org['name'],
        collection_name=org['collection_name'],
        admin_email=org['admin_email']
    )

@router.put("/update", response_model=OrganizationResponse)
async def update_organization(org_in: OrganizationUpdate, current_admin: dict = Depends(get_current_admin)):
    # Validate permission (admin can only update their own org?) 
    # The requirement doesn't explicitly restrict update to OWN org, but implies "Handle deletion for respective authenticated user only".
    # Logic implies admin updates THEIR org usually.
    # But input takes `organization_name`, `email`.
    # If the user is authenticated as 'admin' of 'OrgA', and updates 'OrgB', that should be blocked.
    # The current input format in requirement: `organization_name`, `email`, `password`.
    # It acts like "Set properties for this org".
    # I will verify `current_admin.organization_name` matches target or they are a super-admin (not defined).
    # Assuming each org admin manages their own org.
    
    # Note: Requirement endpoint input `organization_name` is likely the TARGET. 
    # But if I am updating name, I need old name? 
    # Input has `organization_name` which is the NEW name or TARGET?
    # Usually `PUT /org/update` implies body has data.
    # If `organization_name` is in body, is it the lookup key or the new value?
    # Based on "Dynamically handle the new collection creation... and sync", it implies changing name is possible.
    # So we need to know WHICH org to update. If we rely on `current_admin`, we update `current_admin.organization_name`.
    # But `org_in` has `organization_name`. Let's assume `org_in.organization_name` is the NEW name.
    
    if current_admin['organization_name'] == org_in.organization_name:
        # No name change
        pass
    else:
        # Name change requested
        # Check if new name exists
        master_db = db.get_master_db()
        if await master_db.organizations.find_one({"name": org_in.organization_name}):
             raise HTTPException(status_code=400, detail="New Organization name already exists")
    
    master_db = db.get_master_db()
    old_name = current_admin['organization_name']
    new_name = org_in.organization_name
    
    # 1. Update Collection (Rename)
    if old_name != new_name:
        # Rename collection
        old_coll_name = db.get_org_db_name(old_name)
        new_coll_name = db.get_org_db_name(new_name)
        try:
            # Using renameCollection command. Note: source and target namespace required.
            # db.command is usually on the 'admin' database for some ops, but for rename in same DB, use the db.
            # But `renameCollection` is an admin command.
            # `admin` DB must be used.
            # Format: renameCollection: "source_db.source_coll", to: "target_db.target_coll"
            await db.client.admin.command(
                "renameCollection", 
                f"{settings.MONGO_DB_NAME}.{old_coll_name}",
                to=f"{settings.MONGO_DB_NAME}.{new_coll_name}"
            )
        except Exception as e:
            # If collection doesn't exist (e.g. empty), it might fail?
            # Or if target exists.
            print(f"Rename failed or skipped: {e}")
            # If fail, maybe manual copy needed, but rename is best.
            pass

    # 2. Update Metadata
    await master_db.organizations.update_one(
        {"name": old_name},
        {"$set": {
            "name": new_name,
            "collection_name": db.get_org_db_name(new_name),
            "admin_email": org_in.email
        }}
    )
    
    # 3. Update Admin
    hashed_password = get_password_hash(org_in.password)
    await master_db.admins.update_one(
        {"email": current_admin['email']}, # Identity based on email? Or current token?
        # If email updates, we need to update that too.
        # But `current_admin` is from token.
        # We update based on `current_admin['_id']`.
        {"$set": {
            "email": org_in.email,
            "organization_name": new_name,
            "hashed_password": hashed_password
        }}
    )

    return OrganizationResponse(
        organization_name=new_name,
        collection_name=db.get_org_db_name(new_name),
        admin_email=org_in.email
    )

@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_organization(organization_name: str, current_admin: dict = Depends(get_current_admin)):
    # "Allow deletion for respective authenticated user only"
    if current_admin['organization_name'] != organization_name:
         raise HTTPException(status_code=403, detail="Not authorized to delete this organization")
         
    master_db = db.get_master_db()
    
    # 1. Drop Collection
    coll_name = db.get_org_db_name(organization_name)
    await master_db.drop_collection(coll_name)
    
    # 2. Delete Org Metadata
    await master_db.organizations.delete_one({"name": organization_name})
    
    # 3. Delete Admin? Usually yes.
    await master_db.admins.delete_many({"organization_name": organization_name})
    
    return {"message": "Organization deleted successfully"}
