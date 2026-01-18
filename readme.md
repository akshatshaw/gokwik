# GoKwik Intern Assignment Projects

This repository contains a collection of three AI-powered projects developed for the GoKwik internship assignment. These projects demonstrate various capabilities ranging from Retrieval Augmented Generation (RAG) to visual agentic workflows.

## Projects Overview

### 1. AgenticRAG

A sophisticated RAG system leveraging Google ADK and tool-calling agents. This project uses Streamlit for the user interface and ChromaDB for vector storage, allowing for intelligent querying and interaction with documents.

- **Tech Stack:** Python, Streamlit, ChromaDB, Google ADK, LangChain.
- **Key Feature:** Tool-calling capabilities for enhanced agent responses.

### 2. Drag & Drop Agentic UI (`drag-drop`)

A visual workflow builder designed for non-technical users. It allows you to connect an AI agent to tools (like web search) via a drag-and-drop interface.

- **Tech Stack:** FastAPI (Backend), HTML/CSS/JS (Frontend), LangChain (Agent Framework), OpenAI GPT-3.5.
- **Key Feature:** Visual canvas for wiring Tool → Agent pipelines with real-time feedback.

### 3. RAG (`rag`)

A dedicated Document-Based Q&A System. This application enables users to upload documents and ask questions, receiving accurate answers grounded in the provided text.

- **Tech Stack:** Streamlit, LangChain, OpenAI, ChromaDB.
- **Key Feature:** Source citations and precise document parsing.

---

## Installation & Setup Guide

This repository uses **[uv](https://github.com/astral-sh/uv)** for extremely fast Python package management.

### Prerequisites

1.  **Install `uv`** (if not already installed):

    ```bash
    # On Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex

    # On macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd gokwik
    ```

### Running the Projects

Each project is self-contained with its own dependency configuration. Follow the steps below for the specific project you want to run.

#### Option 1: Run AgenticRAG

1.  Navigate to the directory:
    ```bash
    cd AgenticRAG
    ```
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Set up environment variables:
    - Create a `.env` file and add necessary keys (`OPENAI_API_KEY` as required by the code).
4.  Run the application:
    ```bash
    uv run streamlit run app/streamlit_app.py
    ```

#### Option 2: Run Drag & Drop UI

1.  Navigate to the directory:
    ```bash
    cd drag-drop
    ```
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Set up environment variables:
    - Create a `.env` file from `.env.example` (if available) or add your `OPENAI_API_KEY`.
    ```bash
    OPENAI_API_KEY=your_key_here
    ```
4.  Run the application:
    ```bash
    uv run app.py
    ```

    - The server will start at `http://127.0.0.1:8000`.

#### Option 3: Run RAG System

1.  Navigate to the directory:
    ```bash
    cd RAG
    ```
2.  Install dependencies:
    ```bash
    uv sync
    ```
3.  Set up environment variables:
    - Create a `.env` file and add your `OPENAI_API_KEY`.
4.  Run the application:
    ```bash
    uv run streamlit run core/app.py
    ```

---

## Notes

- Ensure you have valid API keys for OpenAI and other services where required.
- The `drag-drop` project may depend on utilities from `AgenticRAG` folder, so keep the directory structure intact.
