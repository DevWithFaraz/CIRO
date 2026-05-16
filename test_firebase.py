import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv('backend/.env')

cred_path = os.getenv("FIREBASE_CRED_PATH")
# The env has FIREBASE_CRED_PATH=./firebase_credentials.json, which is relative to wherever we run.
# If we run from backend, it's ./firebase_credentials.json. If from root, backend/firebase_credentials.json.
# Let's adjust to run from root:
cred_path = "backend/" + cred_path.replace('./', '')

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

doc_ref = db.collection('test_collection').document('test_doc')
doc_ref.set({
    'status': 'success',
    'message': 'Firebase is working!'
})

doc = doc_ref.get()
print("Read document:", doc.to_dict())

# Clean up
doc_ref.delete()
print("Test completed and cleaned up.")
