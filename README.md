Shortest Shop Recommendation System

This project implements a semantic + geographic shop recommendation system using Django, PostgreSQL, pgvector, and Redis. It provides fast and accurate shop recommendations based on user queries and location.

Algorithm: Shortest Shop

The system finds the best shop using a combination of semantic similarity and geographic proximity.

Key Components

1. retrieve_shops function

Retrieves candidate shops from the database with optional filtering:

Steps:

Convert the user query into a vector embedding (embed_text).

Pre-filter shops by category (if provided).

Annotate each shop with cosine distance to the query embedding using pgvector.

Compute geographic distance from the user using the Haversine formula.

Compute a combined score:

combined_score = semantic_distance + (geo_distance / 10)

Sort by combined score and return the top 5 shops.

2. shortest_shop_agent function

Selects the single best shop based on retrieved candidates:

Steps:

Retrieve candidate shops using retrieve_shops.

Compute the combined score for each shop.

Skip shops outside the geographic cutoff.

Select the shop with the lowest combined score.

Return detailed info:

Shop name

Category

Distance from user

Semantic score

Combined score

Why This Algorithm Works:

Semantic search with pgvector captures meaning, not just keywords.

Geographic filtering ensures relevance to user location.

Top-K pre-filtering improves efficiency.

Combined scoring balances relevance and proximity.

CI/CD Workflow (GitHub Actions)

The project uses a two-stage CI/CD pipeline:

1. Build and Test

Services: PostgreSQL with pgvector and Redis.

Dependency caching: Install Python packages before copying source code → faster repeated builds.

Health checks: Wait for DB and Redis readiness.

Tests: Run Django unit tests to ensure code correctness.

2. Build and Push Docker

Disk cleanup to avoid space issues on GitHub runners.

Docker Buildx with caching: Reuse layers for dependencies → faster builds.

Selective Docker push: Only pushes on main branch → PRs run tests only.

Slim Python base image: Smaller image, faster pull times.

Workflow Summary:

Pull Requests → Run only tests for fast feedback.

Push to main / merged PRs → Run full CI/CD including Docker build & push.

Backend and Infrastructure Features

Backend: Django REST Framework

PostgreSQL + pgvector for semantic search

Redis for caching and async tasks

JWT authentication

Rate limiting

Infrastructure / Deployment:

Docker for containerization

NGINX as reverse proxy

GitHub Actions for CI/CD pipeline
