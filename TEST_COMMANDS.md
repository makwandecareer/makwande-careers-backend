# Local tests

After login, use the frontend proxy or a valid bearer token.

## Roadmap

```cmd
curl -X POST http://127.0.0.1:8000/api/ai-career/roadmap ^
-H "Authorization: Bearer YOUR_TOKEN" ^
-H "Content-Type: application/json" ^
-d "{\"target_role\":\"Senior Chemical Engineer\",\"timeframe_months\":18,\"country\":\"South Africa\"}"
```

## Skills gap

```cmd
curl -X POST http://127.0.0.1:8000/api/ai-career/skills-gap ^
-H "Authorization: Bearer YOUR_TOKEN" ^
-H "Content-Type: application/json" ^
-d "{\"target_role\":\"Chemical Engineer\",\"job_description\":\"Paste job description here\"}"
```
