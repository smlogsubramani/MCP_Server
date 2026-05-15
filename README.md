# MCP Server – Azure OpenAI + Microsoft Fabric Demo

This repository contains a lightweight MCP (Model Context Protocol) demo project built using:

- Azure OpenAI
- Azure AI Search
- Microsoft Fabric
- Python

The project is designed to retrieve relevant database metadata, identify related tables, and generate autonomous SQL-based question-answer workflows.

---

# Project Structure

```text
MCP_SERVER/
│
├── App.py
├── upload_metadata.py
├── Retrive_tables_search.py
├── get_index_Data.py
├── clear_index_Data.py
├── requirements.txt
└── .env

AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_DEPLOYMENT=""

FABRIC_CLIENT_ID=""
FABRIC_CLIENT_SECRET=""

AZURE_SEARCH_ENDPOINT=""
AZURE_SEARCH_KEY=""
