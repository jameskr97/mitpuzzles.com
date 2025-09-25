# Backend

## Database Upgrade
```bash
alembic revision --autogenerate -m "create account related tables"
alembic current # view current db state
alembic history # check db history
alembic upgrade head # upgrade to latest
alembic downgrade # go to previous migration
```
