import os

from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="fabric-metadata-index",
    credential=AzureKeyCredential(
        os.getenv("AZURE_SEARCH_KEY")
    )
)

results = client.search(
    search_text="*",
    top=20
)

first_document=client.get_document(9)
print(first_document)

for result in results:
    print("\n====================")
    for key, value in result.items():
        print(f"{key}:")
        print(value)