import os

from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

# =========================================
# AZURE AI SEARCH CONFIG
# =========================================

client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="fabric-metadata-index",
    credential=AzureKeyCredential(
        os.getenv("AZURE_SEARCH_KEY")
    )
)

# =========================================
# GET ALL DOCUMENT IDS
# =========================================

results = client.search(
    search_text="*",
    select=["id"],
    top=1000
)

documents_to_delete = []

for result in results:

    documents_to_delete.append(
        {
            "id": result["id"]
        }
    )

# =========================================
# DELETE DOCUMENTS
# =========================================

if documents_to_delete:

    response = client.delete_documents(documents_to_delete)

    print("ALL DOCUMENTS DELETED")

else:

    print("NO DOCUMENTS FOUND")