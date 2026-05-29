"""
Unit tests for the Comments REST API — fully isolated.
Run with:
    pytest tests/test_comments_api.py -v --cov=tests.comments_api_standalone --cov-report=term-missing
"""

import sys
import json
import uuid
import types
import pathlib
import importlib.util
import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Inject fake modules ONLY for packages not installed (the broken 2016 ones)
# ---------------------------------------------------------------------------
_missing = [
    'oslo_log', 'oslo_config', 'oslo_db',
    'flask_login', 'flask_principal', 'flask_bcrypt',
    'flask_sqlalchemy',
    'jmilkfansblog', 'jmilkfansblog.extensions', 'jmilkfansblog.models',
]
for _name in _missing:
    if _name not in sys.modules:
        sys.modules[_name] = MagicMock()

# Give oslo mocks the attributes the original __init__.py accesses
sys.modules['oslo_log'].log = MagicMock()
sys.modules['oslo_config'].cfg = MagicMock()

# Give jmilkfansblog.extensions a real-looking db object
_fake_db = MagicMock()
sys.modules['jmilkfansblog.extensions'].db = _fake_db

# Give jmilkfansblog.models real-looking model classes
_fake_Comment = MagicMock()
_fake_Post    = MagicMock()
sys.modules['jmilkfansblog.models'].Comment = _fake_Comment
sys.modules['jmilkfansblog.models'].Post    = _fake_Post

# ---------------------------------------------------------------------------
# Load comments_api.py directly from disk (skips jmilkfansblog __init__)
# ---------------------------------------------------------------------------
_api_path = (
    pathlib.Path(__file__).parent.parent
    / 'jmilkfansblog' / 'controllers' / 'flask_restful' / 'comments_api.py'
)
_spec = importlib.util.spec_from_file_location('comments_api_standalone', _api_path)
comments_api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(comments_api)

comments_blueprint = comments_api.comments_blueprint

# ---------------------------------------------------------------------------
# Minimal Flask test app
# ---------------------------------------------------------------------------
from flask import Flask

def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['PROPAGATE_EXCEPTIONS'] = True
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_comment(comment_id=None, post_id=None, name='Alice', text='Nice post!'):
    c = MagicMock()
    c.id   = comment_id or str(uuid.uuid4())
    c.post_id = post_id or str(uuid.uuid4())
    c.name = name
    c.text = text
    c.date = None
    return c

def _make_post(post_id=None, comments=None):
    p = MagicMock()
    p.id       = post_id or str(uuid.uuid4())
    p.comments = comments or []
    return p

BASE = '/api/v1/posts'

# ===========================================================================
# GET /api/v1/posts/<post_id>/comments
# ===========================================================================
class TestListComments:

    def test_list_returns_200_with_comments(self, client):
        pid = str(uuid.uuid4())
        mock_post = _make_post(post_id=pid, comments=[_make_comment(), _make_comment()])
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = mock_post
            resp = client.get(f'{BASE}/{pid}/comments')
        assert resp.status_code == 200
        assert len(json.loads(resp.data)) == 2

    def test_list_returns_empty_list_when_no_comments(self, client):
        pid = str(uuid.uuid4())
        mock_post = _make_post(post_id=pid, comments=[])
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = mock_post
            resp = client.get(f'{BASE}/{pid}/comments')
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_list_returns_404_when_post_not_found(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = None
            resp = client.get(f'{BASE}/{pid}/comments')
        assert resp.status_code == 404

# ===========================================================================
# POST /api/v1/posts/<post_id>/comments
# ===========================================================================
class TestCreateComment:

    def test_create_returns_201_with_valid_payload(self, client):
        pid = str(uuid.uuid4())
        mock_post    = _make_post(post_id=pid)
        new_comment  = _make_comment(post_id=pid, name='Bob', text='Great read!')
        with patch.object(comments_api.Post, 'query') as mq, \
             patch.object(comments_api, 'Comment', return_value=new_comment), \
             patch.object(comments_api, 'db'):
            mq.get.return_value = mock_post
            resp = client.post(f'{BASE}/{pid}/comments',
                               data=json.dumps({'name': 'Bob', 'text': 'Great read!'}),
                               content_type='application/json')
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['name'] == 'Bob'
        assert data['text'] == 'Great read!'

    def test_create_returns_400_when_name_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = _make_post(post_id=pid)
            resp = client.post(f'{BASE}/{pid}/comments',
                               data=json.dumps({'text': 'No name!'}),
                               content_type='application/json')
        assert resp.status_code == 400
        assert 'name' in json.loads(resp.data)['message']

    def test_create_returns_400_when_text_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = _make_post(post_id=pid)
            resp = client.post(f'{BASE}/{pid}/comments',
                               data=json.dumps({'name': 'Carol'}),
                               content_type='application/json')
        assert resp.status_code == 400
        assert 'text' in json.loads(resp.data)['message']

    def test_create_returns_400_when_body_empty(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = _make_post(post_id=pid)
            resp = client.post(f'{BASE}/{pid}/comments',
                               data=json.dumps({}),
                               content_type='application/json')
        assert resp.status_code == 400

    def test_create_returns_404_when_post_not_found(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = None
            resp = client.post(f'{BASE}/{pid}/comments',
                               data=json.dumps({'name': 'Dave', 'text': 'Hi'}),
                               content_type='application/json')
        assert resp.status_code == 404

# ===========================================================================
# GET /api/v1/posts/<post_id>/comments/<comment_id>
# ===========================================================================
class TestGetComment:

    def test_get_returns_200_with_existing_comment(self, client):
        pid = str(uuid.uuid4())
        cid = str(uuid.uuid4())
        mock_comment = _make_comment(comment_id=cid, post_id=pid)
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq:
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = mock_comment
            resp = client.get(f'{BASE}/{pid}/comments/{cid}')
        assert resp.status_code == 200
        assert json.loads(resp.data)['id'] == cid

    def test_get_returns_404_when_post_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = None
            resp = client.get(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}')
        assert resp.status_code == 404

    def test_get_returns_404_when_comment_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq:
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = None
            resp = client.get(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}')
        assert resp.status_code == 404

# ===========================================================================
# PUT /api/v1/posts/<post_id>/comments/<comment_id>
# ===========================================================================
class TestUpdateComment:

    def test_update_name_returns_200(self, client):
        pid = str(uuid.uuid4())
        cid = str(uuid.uuid4())
        mock_comment = _make_comment(comment_id=cid, post_id=pid)
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq, \
             patch.object(comments_api, 'db'):
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = mock_comment
            resp = client.put(f'{BASE}/{pid}/comments/{cid}',
                              data=json.dumps({'name': 'Updated Name'}),
                              content_type='application/json')
        assert resp.status_code == 200
        assert mock_comment.name == 'Updated Name'

    def test_update_text_returns_200(self, client):
        pid = str(uuid.uuid4())
        cid = str(uuid.uuid4())
        mock_comment = _make_comment(comment_id=cid, post_id=pid)
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq, \
             patch.object(comments_api, 'db'):
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = mock_comment
            resp = client.put(f'{BASE}/{pid}/comments/{cid}',
                              data=json.dumps({'text': 'Updated text'}),
                              content_type='application/json')
        assert resp.status_code == 200
        assert mock_comment.text == 'Updated text'

    def test_update_both_fields_returns_200(self, client):
        pid = str(uuid.uuid4())
        cid = str(uuid.uuid4())
        mock_comment = _make_comment(comment_id=cid, post_id=pid)
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq, \
             patch.object(comments_api, 'db'):
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = mock_comment
            resp = client.put(f'{BASE}/{pid}/comments/{cid}',
                              data=json.dumps({'name': 'New', 'text': 'New text'}),
                              content_type='application/json')
        assert resp.status_code == 200

    def test_update_returns_404_when_post_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = None
            resp = client.put(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}',
                              data=json.dumps({'text': 'x'}),
                              content_type='application/json')
        assert resp.status_code == 404

    def test_update_returns_404_when_comment_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq:
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = None
            resp = client.put(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}',
                              data=json.dumps({'text': 'x'}),
                              content_type='application/json')
        assert resp.status_code == 404

# ===========================================================================
# DELETE /api/v1/posts/<post_id>/comments/<comment_id>
# ===========================================================================
class TestDeleteComment:

    def test_delete_returns_204_on_success(self, client):
        pid = str(uuid.uuid4())
        cid = str(uuid.uuid4())
        mock_comment = _make_comment(comment_id=cid, post_id=pid)
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq, \
             patch.object(comments_api, 'db') as mdb:
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = mock_comment
            resp = client.delete(f'{BASE}/{pid}/comments/{cid}')
        assert resp.status_code == 204
        assert resp.data == b''
        mdb.session.delete.assert_called_once_with(mock_comment)
        mdb.session.commit.assert_called_once()

    def test_delete_returns_404_when_post_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mq:
            mq.get.return_value = None
            resp = client.delete(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}')
        assert resp.status_code == 404

    def test_delete_returns_404_when_comment_missing(self, client):
        pid = str(uuid.uuid4())
        with patch.object(comments_api.Post, 'query') as mpq, \
             patch.object(comments_api.Comment, 'query') as mcq:
            mpq.get.return_value = _make_post(post_id=pid)
            mcq.filter_by.return_value.first.return_value = None
            resp = client.delete(f'{BASE}/{pid}/comments/{str(uuid.uuid4())}')
        assert resp.status_code == 404
