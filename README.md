# Two-Tier Flask + MySQL Guestbook App

A simple learning project demonstrating a **two-tier web application** deployed with
**Docker Compose** and automated via a **Jenkins CI/CD pipeline**.

## Architecture

```
Developer → git push → GitHub → Jenkins (on EC2)
                                    │
                                    ├─ clones repo
                                    ├─ builds Docker image
                                    └─ runs docker-compose up
                                            │
                              ┌─────────────┴─────────────┐
                              │                            │
                        Flask container              MySQL container
                        (port 5000)                  (port 3306)
                              │                            │
                              └──────── app_network ───────┘
```

- **Tier 1 (web):** A Flask app serving a guestbook page. Talks to MySQL to read/write entries.
- **Tier 2 (db):** A MySQL 8.0 database storing guestbook entries in a named Docker volume
  (so data survives container restarts).

## Files

| File | Purpose |
|---|---|
| `app.py` | Flask application code |
| `requirements.txt` | Python dependencies |
| `templates/index.html` | HTML page showing guestbook entries |
| `Dockerfile` | Builds the Flask app into a container (uses gunicorn) |
| `docker-compose.yml` | Defines and links the `web` and `db` containers |
| `init.sql` | Auto-creates the database table on first MySQL startup |
| `.env.example` | Template for required environment variables |
| `Jenkinsfile` | CI/CD pipeline definition (build → deploy → test) |

## Running locally

1. Copy the environment file and fill in your own values:
   ```bash
   cp .env.example .env
   ```
2. Start everything:
   ```bash
   docker-compose up -d --build
   ```
3. Visit **http://localhost:5000** in your browser.
4. Check the health endpoint:
   ```bash
   curl http://localhost:5000/health
   ```
5. Stop everything:
   ```bash
   docker-compose down
   ```

## CI/CD with Jenkins

Every push to the `main` branch on GitHub triggers a webhook that tells Jenkins to:
1. Clone the latest code
2. Build a fresh Docker image
3. Tear down old containers and start new ones with `docker-compose up -d --build`
4. Run an integration test (curl `/health`) to confirm the app is actually working
5. Report success or failure

See the `Jenkinsfile` for the exact pipeline stages.
Thank you