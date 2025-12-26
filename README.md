# Django RAG Backend

This project implements a Django REST API backend that allows users to ask questions such as “Which is the shortest shop in a category?” and get answers using Retrieval-Augmented Generation (RAG) techniques.

RAG combines a knowledge retrieval step with a language model (LLM) step.

The system retrieves relevant information from structured or vectorized data, then uses the LLM to generate a precise answer.

This enables the app to answer user queries over shop data without needing the entire dataset in the LLM.

Core AI Components
Embeddings

Text or metadata (e.g., shop names, categories, descriptions, distances) is converted into vector embeddings using sentence-transformers.

Embeddings allow semantic search in high-dimensional vector space.

Stored in a vector store, currently using FAISS (CPU) or Redis for caching & retrieval.

Vector Retrieval (Retriever)

The retriever performs nearest neighbor search in the vector space.

Steps:

Convert user query into an embedding.

Compare query embedding with stored shop embeddings.

Retrieve the top-k most relevant shops based on similarity.

Vector similarity metric: typically cosine similarity.

## 🚀 Features

- **RAG System**: Combines retrieval-based and generative AI approaches
- **Vector Search**: Efficient similarity search with pgvector
- **JWT Authentication**: Secure API access control
- **Redis Caching**: High-performance response caching
- **Dockerized**: Easy deployment with Docker and Docker Compose
- **NGINX**: Reverse proxy and load balancing
- **CI/CD**: Automated testing and deployment with GitHub Actions

## 🏗️ Architecture

### 1. System Overview

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ Client App │───▶│ NGINX (80) │───▶│ Django (8000) │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘ └────────┬────────┘ │ ▼ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ PostgreSQL │◀───│ pgvector │◀───│ RAG System │ │ (pgvector) │ │ (Vector DB) │ │ │ │ │ │ │ └────────┬────────┘ └─────────────────┘ └─────────────────┘ │ │ ┌─────────────────┐ ┌─────────────────┐ │ │ │ │ │ │ │ Redis │◀───│ Cache │◀──────────┘ │ (Caching) │ │ │ │ │ │ │ └─────────────────┘ └─────────────────┘

### 2. Technology Stack

#### Backend

- **Django 4.2**: High-level Python web framework
- **Django REST Framework**: For building Web APIs
- **Django REST Framework Simple JWT**: For JWT authentication

#### Database

- **PostgreSQL 15**: Primary database
- **pgvector**: For vector similarity search
- **Redis**: For caching and rate limiting

#### AI/ML

- **RAG System**: Combines retrieval and generation
- **Sentence Transformers**: For generating document embeddings
- **LangChain**: For building the RAG pipeline

#### Infrastructure

- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **NGINX**: Reverse proxy and load balancer

#### CI/CD

- **GitHub Actions**: For CI/CD pipeline
- **Automated Testing**: Unit and integration tests
- **Automated Deployment**: To staging/production

### 3. Data Flow

1. **Request Handling**:

   - Client sends request to NGINX
   - NGINX forwards to Django app
   - Middleware processes the request

2. **RAG Processing**:

   - Query is converted to embedding
   - Vector search finds relevant documents
   - Context is passed to the language model
   - Response is generated and returned

3. **Caching**:
   - Common queries are cached in Redis
   - Subsequent identical requests are served from cache

This project uses uv
for managing the Python environment and dependencies.

Why uv?

Unified environment + dependency management: uv combines virtual environment creation, dependency resolution, and lockfile management in a single tool.

Lockfile support (uv.lock): Ensures reproducible installs across machines and Docker containers.

Automatic Python selection: uv can pin a specific Python version (e.g., Python 3.14) for the project.

Sync from pyproject.toml or requirements.txt: Makes installation consistent and traceable.
