import os
import pandas as pd
import sqlalchemy as sa

from dotenv import load_dotenv

from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

# =========================================
# FABRIC CONNECTION
# =========================================

SQL_ENDPOINT = "ykoqsjeytl7epm6lvti2gvckou-athatavjqy6urj4alwct7qhaem.datawarehouse.fabric.microsoft.com"

DATABASE = "WT_LH_Silver"

CLIENT_ID = os.getenv("FABRIC_CLIENT_ID")
CLIENT_SECRET = os.getenv("FABRIC_CLIENT_SECRET")

connection_string = (
    f"mssql+pyodbc://{CLIENT_ID}:{CLIENT_SECRET}"
    f"@{SQL_ENDPOINT}:1433/{DATABASE}"
    f"?driver=ODBC+Driver+18+for+SQL+Server"
    f"&authentication=ActiveDirectoryServicePrincipal"
    f"&Encrypt=yes"
    f"&TrustServerCertificate=no"
)

engine = sa.create_engine(connection_string)

# =========================================
# AZURE AI SEARCH
# =========================================

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="fabric-metadata-index",
    credential=AzureKeyCredential(
        os.getenv("AZURE_SEARCH_KEY")
    )
)

# =========================================
# LOAD SCHEMA
# =========================================

query = """
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE
(
    TABLE_SCHEMA = 'shopify_prashanti'
    AND TABLE_NAME IN (
        'customers',
        'customers_addresses',
        'customer_journey',
        'orders',
        'orders_agreements',
        'orders_lineitems',
        'orders_prices',
        'orders_addresses'
    )
)
ORDER BY TABLE_SCHEMA, TABLE_NAME
"""

df = pd.read_sql(query, engine)

# =========================================
# CREATE DOCUMENTS
# =========================================

documents = []

grouped = df.groupby(["TABLE_SCHEMA", "TABLE_NAME"])

counter = 1

for (schema, table), group in grouped:

    column_text = ""

    for _, row in group.iterrows():

        column_text += (
            f"{row['COLUMN_NAME']} "
            f"({row['DATA_TYPE']})\n"
        )

    content = f"""
    Table Name: {schema}.{table}

    Columns:
    {column_text}
    """

    documents.append(
        {
            "id": str(counter),
            "table_name": table,
            "description": f"Metadata for {table}",
            "columns": column_text,
            "content": content
        }
    )

    counter += 1

# =========================================
# UPLOAD DOCUMENTS
# =========================================

result = search_client.upload_documents(documents)

print("UPLOAD SUCCESS")
print(result)