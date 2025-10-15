pip install -r requirements.txt
instalar dependencias y luego ⤵️

```docker compose up  ```

```docker compose exec api python -m app.scripts.faker_seed```

### probar ETL

docker compose exec api python etl/run_etl.py