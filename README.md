# Comments REST API — IT6 Final Drill

> **Student addition** to [Cyzenzz/blog-web-application](https://github.com/Cyzenzz/blog-web-application)
> (originally by [JmilkFan](https://github.com/JmilkFan/blog-web-application), first commit 2016)

---

## What was added

A complete **Comments REST API** (`feature/comments-api` branch) that exposes full CRUD
operations for blog-post comments. The original application has a `Comment` model and
displays comments via HTML templates, but had **no REST endpoint** for them.

---

## New files

| File | Purpose |
|---|---|
| `jmilkfansblog/controllers/flask_restful/comments_api.py` | Blueprint + 5 endpoints |
| `tests/test_comments_api.py` | 18 unit tests, 100 % coverage |

---

## API Endpoints

Base URL: `http://<host>:<api_port>`

| Method | URL | Description | Success code |
|--------|-----|-------------|--------------|
| `GET` | `/api/v1/posts/<post_id>/comments` | List all comments for a post | `200` |
| `POST` | `/api/v1/posts/<post_id>/comments` | Create a new comment | `201` |
| `GET` | `/api/v1/posts/<post_id>/comments/<id>` | Retrieve a single comment | `200` |
| `PUT` | `/api/v1/posts/<post_id>/comments/<id>` | Update a comment | `200` |
| `DELETE` | `/api/v1/posts/<post_id>/comments/<id>` | Delete a comment | `204` |

### Request / Response format (JSON)

**Create / Update body**
```json
{
  "name": "Alice",
  "text": "Great post, learned a lot!"
}
```

**Response body (single comment)**
```json
{
  "id": "3f2a...",
  "name": "Alice",
  "text": "Great post, learned a lot!",
  "post_id": "7c1b...",
  "date": "2025-01-15T10:30:00"
}
```

### HTTP status codes used

| Code | Meaning |
|------|---------|
| `200` | OK — successful GET or PUT |
| `201` | Created — successful POST |
| `204` | No Content — successful DELETE |
| `400` | Bad Request — missing required field |
| `404` | Not Found — post or comment does not exist |

---

## Registering the blueprint

In `jmilkfansblog/app.py` (or wherever blueprints are registered), add:

```python
from jmilkfansblog.controllers.flask_restful.comments_api import comments_blueprint

def create_app(object_name):
    app = Flask(__name__)
    # ... existing setup ...
    app.register_blueprint(comments_blueprint)
    return app
```

---

## Running the tests

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run with coverage report
pytest tests/test_comments_api.py -v --cov=jmilkfansblog.controllers.flask_restful.comments_api --cov-report=term-missing
```

Expected output: **18 passed**, coverage **100 %**.

---

## Why Comments?

The original app already models `Comment` with `name`, `text`, `post_id`, and `date`
columns (see `jmilkfansblog/models.py`). Exposing these via a REST API allows:

- **Mobile / SPA clients** to post and retrieve comments without loading full HTML pages.
- **Third-party integrations** (e.g. a mobile app, Slack bot) to interact with comments.
- **Moderation tooling** to update or delete comments programmatically.

It is a natural, high-value addition that fits the existing data model with zero schema
changes required.

---

## Original repository

<https://github.com/JmilkFan/blog-web-application>

Forked by Cycy-newb: <https://github.com/Cycy-newb/blog-web-application>
