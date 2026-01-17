# Architecture & Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                     (Streamlit Web App)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  API Key     │  │   Document   │  │  Chat Input  │         │
│  │  Input       │  │   Loader     │  │   & History  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│                                                                   │
│  ┌────────────────────┐         ┌─────────────────────┐        │
│  │ DocumentProcessor  │         │     QASystem        │        │
│  │  - Load docs       │         │  - Create chain     │        │
│  │  - Split chunks    │         │  - Retrieve docs    │        │
│  │  - Create vectors  │         │  - Generate answer  │        │
│  └────────────────────┘         └─────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────────┐         │
│  │   ChromaDB       │         │   Local Documents    │         │
│  │ (Vector Store)   │         │   (./documents/)     │         │
│  │  - Embeddings    │         │   - .txt files       │         │
│  │  - Fast search   │         │   - Sample data      │         │
│  └──────────────────┘         └──────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              OpenAI API                                  │   │
│  │  - text-embedding-ada-002 (for embeddings)             │   │
│  │  - gpt-3.5-turbo (for answer generation)               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow - Document Loading

```
1. USER ACTION
   │
   ├─→ Clicks "Load Documents" in Streamlit UI
   │
   ▼
2. DOCUMENT PROCESSOR
   │
   ├─→ Scans ./documents/ folder for .txt files
   ├─→ Loads all documents
   ├─→ Splits into chunks (1000 chars, 200 overlap)
   │
   ▼
3. EMBEDDING CREATION
   │
   ├─→ Sends chunks to OpenAI API
   ├─→ Gets vector embeddings (1536 dimensions)
   │
   ▼
4. VECTOR STORAGE
   │
   ├─→ Stores embeddings in ChromaDB
   ├─→ Includes metadata (source file, content)
   │
   ▼
5. CONFIRMATION
   │
   └─→ Shows success message to user
```

## Data Flow - Question Answering

```
1. USER QUESTION
   │
   ├─→ "What is the pricing for Professional plan?"
   │
   ▼
2. EMBEDDING CONVERSION
   │
   ├─→ Convert question to vector embedding
   ├─→ Use OpenAI text-embedding-ada-002
   │
   ▼
3. SIMILARITY SEARCH
   │
   ├─→ Search ChromaDB for similar vectors
   ├─→ Retrieve top 3 most similar chunks
   │   Example results:
   │   - Chunk 1: "Professional Plan: $299/month..."
   │   - Chunk 2: "...up to 50 users with..."
   │   - Chunk 3: "...Professional Plan features include..."
   │
   ▼
4. CONTEXT PREPARATION
   │
   ├─→ Format retrieved chunks
   ├─→ Create prompt with context + question
   │
   ▼
5. LLM GENERATION
   │
   ├─→ Send to GPT-3.5-turbo with prompt:
   │   "Answer ONLY based on this context..."
   │   Context: [retrieved chunks]
   │   Question: "What is the pricing..."
   │
   ├─→ LLM generates grounded answer
   │
   ▼
6. RESPONSE FORMATTING
   │
   ├─→ Extract answer text
   ├─→ Attach source documents
   ├─→ Format for display
   │
   ▼
7. UI DISPLAY
   │
   ├─→ Show answer in chat
   ├─→ Display source citations
   └─→ Add to chat history
```

## Component Interactions

```
┌──────────────────────────────────────────────────────────────┐
│  app.py (Streamlit UI)                                       │
│                                                              │
│  ├─ initialize_session_state()                              │
│  │   └─ Manages: vector_store, qa_system, messages         │
│  │                                                          │
│  ├─ load_documents(api_key)                                │
│  │   └─→ DocumentProcessor.load_documents()                │
│  │   └─→ DocumentProcessor.split_documents()               │
│  │   └─→ DocumentProcessor.create_vector_store()           │
│  │                                                          │
│  └─ Chat Loop                                               │
│      ├─ User input → question                               │
│      └─→ QASystem.ask(question)                            │
│          └─ Returns: {answer, sources}                      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  document_processor.py                                       │
│                                                              │
│  └─ DocumentProcessor                                        │
│      ├─ load_documents()                                     │
│      │   └─ Uses: DirectoryLoader + TextLoader              │
│      ├─ split_documents()                                    │
│      │   └─ Uses: RecursiveCharacterTextSplitter            │
│      └─ create_vector_store()                                │
│          └─ Uses: OpenAIEmbeddings + ChromaDB               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  qa_system.py                                                │
│                                                              │
│  └─ QASystem                                                 │
│      ├─ __init__()                                           │
│      │   └─ Creates: retriever, prompt, llm                 │
│      ├─ format_docs()                                        │
│      │   └─ Joins document contents                         │
│      └─ ask(question)                                        │
│          ├─ Retrieve relevant docs                          │
│          ├─ Create LCEL chain                               │
│          ├─ Invoke LLM                                       │
│          └─ Return: {answer, sources}                       │
└──────────────────────────────────────────────────────────────┘
```

## Key Technologies

### LangChain Components Used

```
langchain_text_splitters
├─ RecursiveCharacterTextSplitter    # Document chunking

langchain_community
├─ DirectoryLoader                   # Load directory of files
├─ TextLoader                        # Load .txt files
└─ Chroma                           # Vector database

langchain_openai
├─ OpenAIEmbeddings                 # Create embeddings
└─ ChatOpenAI                       # LLM for generation

langchain_core
├─ Document                         # Document schema
├─ PromptTemplate                   # Prompt management
├─ StrOutputParser                  # Parse LLM output
└─ RunnablePassthrough              # Chain utilities
```

### Streamlit Components Used

```
streamlit
├─ st.set_page_config()             # Page configuration
├─ st.title() / st.header()         # Headers
├─ st.sidebar                       # Sidebar elements
├─ st.text_input()                  # API key input
├─ st.button()                      # Action buttons
├─ st.chat_message()                # Chat display
├─ st.chat_input()                  # Chat input
├─ st.expander()                    # Expandable sections
├─ st.spinner()                     # Loading indicators
└─ st.session_state                 # State management
```

## Prompt Engineering

### Custom Prompt Template

```
System Instructions:
├─ "Answer ONLY based on provided context"
├─ "Say 'I don't know' if info not in context"
├─ "Cite document sources"
├─ "Be concise and direct"
└─ "No inference beyond stated facts"

Input Variables:
├─ {context}    # Retrieved document chunks
└─ {question}   # User's question

Output Format:
└─ "Answer (with source citation):"
```

## Security & Best Practices

```
✓ API Key Handling
  └─ Never stored in code
  └─ Password field input
  └─ Passed directly to API calls

✓ Error Handling
  └─ Try-catch blocks
  └─ User-friendly error messages
  └─ Validation checks

✓ Data Privacy
  └─ Local vector storage
  └─ No data persistence beyond session
  └─ Only OpenAI sees query data

✓ Performance
  └─ Efficient chunk size (1000 chars)
  └─ Limited retrieval (top 3 docs)
  └─ Temperature=0 (consistent output)
```

## File Relationships

```
pyproject.toml
  └─→ Defines all dependencies
       └─→ Installed via: uv sync

app.py
  ├─→ imports document_processor
  ├─→ imports qa_system
  └─→ imports config

document_processor.py
  ├─→ Reads from: ./documents/
  └─→ Writes to: ./chroma_db/

qa_system.py
  └─→ Reads from: ./chroma_db/

config.py
  └─→ Shared configuration constants

test_setup.py
  └─→ Validates entire setup
```

---

This architecture ensures:

- **Modularity**: Clear separation of concerns
- **Maintainability**: Easy to update components
- **Scalability**: Can add more document types easily
- **Testability**: Components can be tested independently
- **Security**: Proper API key and data handling
