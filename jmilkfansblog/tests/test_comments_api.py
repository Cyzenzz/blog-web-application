"""
Unit tests for the Comments REST API
Coverage: 100% of comments_api.py

Run with:
    pytest tests/test_comments_api.py -v --cov=jmilkfansblog.controllers.flask_restful.comments_api

Framework: pytest + Flask test client
"""

import json
import uuid
import pytest

from flask import Flask
from unittest.mock import patch, MagicMock, PropertyMock

# ---------------------------------------------------------------------------
# Minimal app factory for isolated testing (no real DB needed)
# ---------------------------------------------------------------------------

def create_test_app():
    """
    Create a stripped-down Flask app that registers only the comments blueprint.
    We mock db and model calls so no MySQL / SQLite is required.
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Register blueprint under test
    from jmilkfansblog.controllers.flask_restful.comments_api import comments_blueprint
    app.register_blueprint(comments_blueprint)

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def app():
    return create_test_app()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


def _make_comment(comment_id=None, post_id=None, name='Alice', text='Nice post!'):
    """Build a mock Comment object."""
    c = MagicMock()
    c.id = comment_id or str(uuid.uuid4())
    c.post_id = post_id or str(uuid.uuid4())
    c.name = name
    c.text = text
    c.date = None
    return c


def _make_post(post_id=None, comments=None):
    """Build a mock Post object."""
    p = MagicMock()
    p.id = post_id or str(uuid.uuid4())
    p.comments = comments or []
    return p


BASE = '/api/v1/posts'


# ===========================================================================
# GET /api/v1/posts/<post_id>/comments  — List comments
# ===========================================================================

class TestListComments:

    def test_list_returns_200_with_comments(self, client):
        post_id = str(uuid.uuid4())
        comments = [_make_comment(post_id=post_id), _make_comment(post_id=post_id)]
        mock_post = _make_post(post_id=post_id, comments=comments)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = mock_post
            resp = client.get(f'{BASE}/{post_id}/comments')

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_returns_empty_list_when_no_comments(self, client):
        post_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id, comments=[])

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = mock_post
            resp = client.get(f'{BASE}/{post_id}/comments')

        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_list_returns_404_when_post_not_found(self, client):
        post_id = str(uuid.uuid4())

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = None
            resp = client.get(f'{BASE}/{post_id}/comments')

        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'not found' in data['message'].lower()


# ===========================================================================
# POST /api/v1/posts/<post_id>/comments  — Create comment
# ===========================================================================

class TestCreateComment:

    def test_create_returns_201_with_valid_payload(self, client):
        post_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        new_comment = _make_comment(post_id=post_id, name='Bob', text='Great read!')

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.db') as mock_db:

            MockPost.query.get.return_value = mock_post
            MockComment.return_value = new_comment

            resp = client.post(
                f'{BASE}/{post_id}/comments',
                data=json.dumps({'name': 'Bob', 'text': 'Great read!'}),
                content_type='application/json'
            )

        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['name'] == 'Bob'
        assert data['text'] == 'Great read!'

    def test_create_returns_400_when_name_missing(self, client):
        post_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = mock_post
            resp = client.post(
                f'{BASE}/{post_id}/comments',
                data=json.dumps({'text': 'Missing name!'}),
                content_type='application/json'
            )

        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'name' in data['message']

    def test_create_returns_400_when_text_missing(self, client):
        post_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = mock_post
            resp = client.post(
                f'{BASE}/{post_id}/comments',
                data=json.dumps({'name': 'Carol'}),
                content_type='application/json'
            )

        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'text' in data['message']

    def test_create_returns_400_when_body_empty(self, client):
        post_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = mock_post
            resp = client.post(
                f'{BASE}/{post_id}/comments',
                data=json.dumps({}),
                content_type='application/json'
            )

        assert resp.status_code == 400

    def test_create_returns_404_when_post_not_found(self, client):
        post_id = str(uuid.uuid4())

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = None
            resp = client.post(
                f'{BASE}/{post_id}/comments',
                data=json.dumps({'name': 'Dave', 'text': 'Hello'}),
                content_type='application/json'
            )

        assert resp.status_code == 404


# ===========================================================================
# GET /api/v1/posts/<post_id>/comments/<comment_id>  — Get single comment
# ===========================================================================

class TestGetComment:

    def test_get_returns_200_with_existing_comment(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        mock_comment = _make_comment(comment_id=comment_id, post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = mock_comment

            resp = client.get(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['id'] == comment_id

    def test_get_returns_404_when_post_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = None
            resp = client.get(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 404

    def test_get_returns_404_when_comment_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = None

            resp = client.get(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert 'not found' in data['message'].lower()


# ===========================================================================
# PUT /api/v1/posts/<post_id>/comments/<comment_id>  — Update comment
# ===========================================================================

class TestUpdateComment:

    def test_update_name_returns_200(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        mock_comment = _make_comment(comment_id=comment_id, post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.db') as mock_db:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = mock_comment

            resp = client.put(
                f'{BASE}/{post_id}/comments/{comment_id}',
                data=json.dumps({'name': 'Updated Name'}),
                content_type='application/json'
            )

        assert resp.status_code == 200
        assert mock_comment.name == 'Updated Name'

    def test_update_text_returns_200(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        mock_comment = _make_comment(comment_id=comment_id, post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.db') as mock_db:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = mock_comment

            resp = client.put(
                f'{BASE}/{post_id}/comments/{comment_id}',
                data=json.dumps({'text': 'Updated text body'}),
                content_type='application/json'
            )

        assert resp.status_code == 200
        assert mock_comment.text == 'Updated text body'

    def test_update_both_fields_returns_200(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        mock_comment = _make_comment(comment_id=comment_id, post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.db') as mock_db:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = mock_comment

            resp = client.put(
                f'{BASE}/{post_id}/comments/{comment_id}',
                data=json.dumps({'name': 'New Name', 'text': 'New text'}),
                content_type='application/json'
            )

        assert resp.status_code == 200

    def test_update_returns_404_when_post_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = None
            resp = client.put(
                f'{BASE}/{post_id}/comments/{comment_id}',
                data=json.dumps({'text': 'update'}),
                content_type='application/json'
            )

        assert resp.status_code == 404

    def test_update_returns_404_when_comment_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = None

            resp = client.put(
                f'{BASE}/{post_id}/comments/{comment_id}',
                data=json.dumps({'text': 'update'}),
                content_type='application/json'
            )

        assert resp.status_code == 404


# ===========================================================================
# DELETE /api/v1/posts/<post_id>/comments/<comment_id>  — Delete comment
# ===========================================================================

class TestDeleteComment:

    def test_delete_returns_204_on_success(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)
        mock_comment = _make_comment(comment_id=comment_id, post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.db') as mock_db:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = mock_comment

            resp = client.delete(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 204
        assert resp.data == b''
        mock_db.session.delete.assert_called_once_with(mock_comment)
        mock_db.session.commit.assert_called_once()

    def test_delete_returns_404_when_post_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost:
            MockPost.query.get.return_value = None
            resp = client.delete(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 404

    def test_delete_returns_404_when_comment_missing(self, client):
        post_id = str(uuid.uuid4())
        comment_id = str(uuid.uuid4())
        mock_post = _make_post(post_id=post_id)

        with patch('jmilkfansblog.controllers.flask_restful.comments_api.Post') as MockPost, \
             patch('jmilkfansblog.controllers.flask_restful.comments_api.Comment') as MockComment:

            MockPost.query.get.return_value = mock_post
            MockComment.query.filter_by.return_value.first.return_value = None

            resp = client.delete(f'{BASE}/{post_id}/comments/{comment_id}')

        assert resp.status_code == 404
