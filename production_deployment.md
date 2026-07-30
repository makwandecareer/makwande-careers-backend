# Phase 5.10 - Production Deployment Guide

## Recommended Stack

- FastAPI + Uvicorn/Gunicorn
- PostgreSQL
- Redis
- Nginx
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Let's Encrypt TLS
- Object Storage (AWS S3 / Azure Blob / MinIO)

## Docker Services

services:
  api:
  postgres:
  redis:
  nginx:

## Environment Variables

APP_ENV=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your_key
PAYSTACK_SECRET_KEY=your_key
SECRET_KEY=replace_with_secure_random_value

## Deployment Checklist

- [ ] HTTPS enabled
- [ ] Automatic database migrations
- [ ] Daily backups
- [ ] Structured logging
- [ ] Health checks
- [ ] Rate limiting
- [ ] Monitoring & alerting
- [ ] CDN for static assets
- [ ] Email service configured
- [ ] Background workers running
- [ ] Payment webhooks verified
- [ ] Secrets stored securely
- [ ] API documentation enabled
- [ ] Disaster recovery plan tested

## CI/CD Pipeline

1. Run linting
2. Run unit tests
3. Run integration tests
4. Build Docker image
5. Push image to registry
6. Deploy to staging
7. Run smoke tests
8. Deploy to production
9. Verify health endpoint
10. Roll back automatically on failure

## Monitoring

Track:
- API latency
- Error rates
- Database performance
- Queue length
- AI request volume
- Payment failures
- CPU and memory usage
- Disk usage
- Active users
- Subscription conversions

This guide serves as the production deployment blueprint for the Makwande Careers platform.
