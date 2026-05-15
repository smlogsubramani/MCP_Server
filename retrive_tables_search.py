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

question = input("Ask Question: ")

results = client.search(
    search_text=question,
    top=5
)

for result in results:

    print("\n===================")

    print("TABLE:")
    print(result["table_name"])

    print("\nCONTENT:")
    print(result["content"])