import os
import pandas as pd
import sqlalchemy as sa
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

# =========================================
# AZURE OPENAI CONFIG
# =========================================

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

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

engine = sa.create_engine(
    connection_string,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=30,
    pool_size=5,
    max_overflow=10
)
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
# LOAD SCHEMA METADATA
# =========================================

def load_schema_metadata():

    query = """
    SELECT
        TABLE_SCHEMA,
        TABLE_NAME,
        COLUMN_NAME,    
        DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    ORDER BY TABLE_SCHEMA, TABLE_NAME
    """

    df = pd.read_sql(query, engine)

    schema_text = ""

    grouped = df.groupby(["TABLE_SCHEMA", "TABLE_NAME"])

    for (schema, table), group in grouped:

        schema_text += f"\nTable: {schema}.{table}\n"

        for _, row in group.iterrows():
            schema_text += (
                f" - {row['COLUMN_NAME']} ({row['DATA_TYPE']})\n"
            )

    return schema_text
# =========================================
# RETRIEVE RELEVANT TABLES
# =========================================

def retrieve_relevant_tables(user_question):

    results = search_client.search(
        search_text=user_question,
        top=5
    )

    tables = []

    for result in results:

        table_name = result["table_name"]

        if table_name not in tables:
            tables.append(table_name)

    return tables   

# =========================================
# LOAD ONLY RELEVANT SCHEMA
# =========================================

def load_relevant_schema(relevant_tables):

    table_list = ",".join(
        [f"'{table}'" for table in relevant_tables]
    )

    query = f"""
    SELECT
        TABLE_SCHEMA,
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME IN ({table_list})
    ORDER BY TABLE_SCHEMA, TABLE_NAME
    """

    df = pd.read_sql(query, engine)

    schema_text = ""

    grouped = df.groupby(["TABLE_SCHEMA", "TABLE_NAME"])

    for (schema, table), group in grouped:

        schema_text += f"\nTable: {schema}.{table}\n"

        for _, row in group.iterrows():

            schema_text += (
                f" - {row['COLUMN_NAME']} "
                f"({row['DATA_TYPE']})\n"
            )

    return schema_text


# =========================================
# GENERATE SQL USING AI
# =========================================

def generate_sql(user_question):

    # =====================================
    # RETRIEVE RELEVANT TABLES
    # =====================================

    relevant_tables = retrieve_relevant_tables(
        user_question
    )

    print("\nRelevant Tables:")
    print(relevant_tables)

    # =====================================
    # LOAD ONLY RELEVANT SCHEMA
    # =====================================

    schema_metadata = load_relevant_schema(
        relevant_tables
    )

    # =====================================
    # SYSTEM PROMPT
    # =====================================

    system_prompt = f"""
    You are an enterprise SQL assistant.

    You are connected to Microsoft Fabric Warehouse.

    IMPORTANT RULES:
    - Return ONLY raw SQL query.
    - Do NOT explain anything.
    - Do NOT add markdown.
    - Do NOT add ```sql.
    - Do NOT add comments.
    - Do NOT add English text.
    - Output must start directly with SELECT.

    Rules:
    - Use TOP 100 unless aggregation.
    - Use schema names.
    - Do not hallucinate tables.
    - Use only tables/columns below.

    DATABASE SCHEMA:
    {schema_metadata}
    """

    # =====================================
    # OPENAI CALL
    # =====================================

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        temperature=0
    )

    sql_query = response.choices[0].message.content

    sql_query = (
        sql_query
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

    return sql_query

# =========================================
# EXECUTE SQL
# =========================================

def execute_sql(sql_query):

    try:

        df = pd.read_sql(sql_query, engine)

        return df

    except Exception as e:

        return str(e)

# =========================================
# EXPLAIN RESULTS
# =========================================

def explain_results(user_question, df):

    data_sample = df.head(20).to_string()

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": """
You are a business analyst.

Explain query results clearly for business users.
"""
            },
            {
                "role": "user",
                "content": f"""
User Question:
{user_question}

Query Results:
{data_sample}
"""
            }
        ]
    )

    return response.choices[0].message.content

# =========================================
# MAIN LOOP
# =========================================

while True:

    user_question = input("\nAsk Question: ")

    if user_question.lower() == "exit":
        break

    print("\nGenerating SQL...")

    sql_query = generate_sql(user_question)

    print("\nGenerated SQL:\n")
    print(sql_query)

    print("\nExecuting Query...")

    result = execute_sql(sql_query)

    if isinstance(result, str):

        print("\nERROR:")
        print(result)

    else:

        print("\nResult Preview:")
        print(result.head())

        print("\nGenerating Explanation...")

        explanation = explain_results(
            user_question,
            result
        )

        print("\nAI Explanation:\n")
        print(explanation)