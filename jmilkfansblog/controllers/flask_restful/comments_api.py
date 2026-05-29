"""
REST API for Comments Resource
Branch: feature/comments-api

Adds full CRUD operations for blog post comments.
Endpoints:
  GET    /api/v1/posts/<post_id>/comments          - List all comments for a post
  POST   /api/v1/posts/<post_id>/comments          - Create a new comment
  GET    /api/v1/posts/<post_id>/comments/<id>     - Get a single comment
  PUT    /api/v1/posts/<post_id>/comments/<id>     - Update a comment
  DELETE /api/v1/posts/<post_id>/comments/<id>     - Delete a comment
"""

from datetime import datetime

from flask import Blueprint
from flask_restful import Api, Resource, reqparse, fields, marshal_with, abort

from jmilkfansblog.extensions import db
from jmilkfansblog.models import Comment, Post

# ---------------------------------------------------------------------------
# Blueprint & Api setup
# ---------------------------------------------------------------------------

comments_blueprint = Blueprint('comments_api', __name__)
api = Api(comments_blueprint)

# ---------------------------------------------------------------------------
# Output field definitions (used by marshal_with)
# ---------------------------------------------------------------------------

comment_fields = {
    'id':         fields.String,
    'name':       fields.String,
    'text':       fields.String,
    'post_id':    fields.String,
    'date':       fields.DateTime(dt_format='iso8601'),
}

# ---------------------------------------------------------------------------
# Request parsers
# ---------------------------------------------------------------------------

def _build_parser(require_all=True):
    parser = reqparse.RequestParser()
    parser.add_argument(
        'name', type=str, required=require_all,
        help='Author name is required', location='json'
    )
    parser.add_argument(
        'text', type=str, required=require_all,
        help='Comment text is required', location='json'
    )
    return parser

create_parser = _build_parser(require_all=True)
update_parser = _build_parser(require_all=False)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_post_or_404(post_id):
    """Return a Post or abort with 404."""
    post = Post.query.get(post_id)
    if post is None:
        abort(404, message=f"Post '{post_id}' not found.")
    return post


def _get_comment_or_404(post_id, comment_id):
    """Return a Comment that belongs to the given post, or abort with 404."""
    _get_post_or_404(post_id)
    comment = Comment.query.filter_by(id=comment_id, post_id=post_id).first()
    if comment is None:
        abort(404, message=f"Comment '{comment_id}' not found on post '{post_id}'.")
    return comment

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

class CommentListResource(Resource):
    """
    /api/v1/posts/<post_id>/comments
    """

    @marshal_with(comment_fields)
    def get(self, post_id):
        """List all comments for a post (200)."""
        post = _get_post_or_404(post_id)
        return post.comments, 200

    @marshal_with(comment_fields)
    def post(self, post_id):
        """Create a new comment on a post (201)."""
        _get_post_or_404(post_id)
        args = create_parser.parse_args(strict=True)

        comment = Comment(
            name=args['name'].strip(),
            text=args['text'].strip(),
            post_id=post_id,
            date=datetime.utcnow(),
        )
        db.session.add(comment)
        db.session.commit()
        return comment, 201


class CommentResource(Resource):
    """
    /api/v1/posts/<post_id>/comments/<comment_id>
    """

    @marshal_with(comment_fields)
    def get(self, post_id, comment_id):
        """Retrieve a single comment (200)."""
        comment = _get_comment_or_404(post_id, comment_id)
        return comment, 200

    @marshal_with(comment_fields)
    def put(self, post_id, comment_id):
        """Update one or more fields of a comment (200)."""
        comment = _get_comment_or_404(post_id, comment_id)
        args = update_parser.parse_args(strict=True)

        if args['name'] is not None:
            comment.name = args['name'].strip()
        if args['text'] is not None:
            comment.text = args['text'].strip()

        db.session.commit()
        return comment, 200

    def delete(self, post_id, comment_id):
        """Delete a comment (204)."""
        comment = _get_comment_or_404(post_id, comment_id)
        db.session.delete(comment)
        db.session.commit()
        return '', 204


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

api.add_resource(
    CommentListResource,
    '/api/v1/posts/<string:post_id>/comments'
)
api.add_resource(
    CommentResource,
    '/api/v1/posts/<string:post_id>/comments/<string:comment_id>'
)
