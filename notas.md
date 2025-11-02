pip install -r requirements.txt
instalar dependencias y luego ⤵️

```docker compose up  ```

```docker compose exec api python -m app.scripts.faker_seed```

### probar ETL



``` curl -X POST "http://localhost:8000/etl?page_size=250" ```