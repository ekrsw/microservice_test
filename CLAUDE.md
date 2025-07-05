# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Docker Operations
- `docker compose up -d` - Start all services (RabbitMQ, auth-service, user-service, knowledge-service)
- `docker compose down` - Stop all services
- `docker compose logs [service-name]` - View logs for specific service

### Service-Specific Commands
- `cd auth-service && python -m pytest tests/` - Run auth service tests
- `cd user-service && python -m pytest tests/` - Run user service tests
- `cd auth-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` - Run auth service locally
- `cd user-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8080` - Run user service locally

### Database Operations
- `cd auth-service && alembic upgrade head` - Apply database migrations for auth service
- `cd user-service && alembic upgrade head` - Apply database migrations for user service

## Architecture Overview

This is a microservices architecture for a knowledge management system with the following components:

### Services
1. **auth-service** (Port 8080) - Authentication and user management
   - FastAPI application with JWT token authentication
   - PostgreSQL database for user data
   - Redis for session/token caching
   - RabbitMQ messaging for inter-service communication

2. **user-service** (Port varies) - User profile management
   - FastAPI application for user CRUD operations
   - PostgreSQL database for user profiles
   - RabbitMQ messaging integration

3. **knowledge-service** - Knowledge base management
   - FastAPI application for knowledge articles
   - Database integration for article storage

4. **frontend** - Static HTML/CSS/JS frontend
   - Simple web interface for user interactions

### Messaging Architecture
- **RabbitMQ** (Port 5672, Management UI: 15672) - Message broker for inter-service communication
- Services communicate via async message queues
- User creation requests flow: user-service → auth-service
- Response handling via dedicated message handlers

### Database Architecture
- Each service has its own PostgreSQL database instance
- Database migrations managed via Alembic
- Async database operations using SQLAlchemy 2.0 + asyncpg

### Key Technologies
- **FastAPI** - Web framework for all services
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **asyncpg** - PostgreSQL async driver
- **aio-pika** - RabbitMQ async client
- **Redis** - Caching and session storage
- **pytest** - Testing framework

### Service Communication
- REST APIs for external communication
- RabbitMQ message queues for inter-service communication
- JWT tokens for authentication across services
- Public/private key cryptography for token validation

### Testing Strategy
- Comprehensive unit tests in `tests/unit/` directories
- Test coverage for API endpoints, CRUD operations, core functionality
- Use pytest with async support (`pytest-asyncio`)
- Database testing with transaction rollbacks

## Development Notes

### Environment Setup
- Services run in Docker containers with docker-compose
- Environment variables configured via `.env` files
- Each service has its own Docker configuration

### Code Structure
- Each service follows similar FastAPI project structure:
  - `app/api/` - API endpoints and routing
  - `app/core/` - Core functionality (config, logging, security)
  - `app/crud/` - Database operations
  - `app/db/` - Database configuration and sessions
  - `app/models/` - SQLAlchemy models
  - `app/schemas/` - Pydantic schemas
  - `app/messaging/` - RabbitMQ handlers

### Security Features
- JWT token authentication with RS256 algorithm
- Password hashing with bcrypt
- Request validation with Pydantic
- CORS middleware configuration
- Redis-based session management