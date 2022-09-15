import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods = ['GET'])
def get_drinks():
    drinks = Drink.query.all()
    return jsonify({'success': True, 'drinks': [drink.short() for drink in drinks]})


@app.route('/drinks-detail', methods = ['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
    drinks = Drink.query.all()
    return jsonify({'success': True, 'drinks': [drink.long() for drink in drinks]})


@app.route('/drinks', methods = ['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    title = body.get('title', None)
    recipe = body.get('recipe', None)
    if title is None or recipe is None:
        abort(422)
    
    drink = Drink(title=title, recipe=json.dumps([recipe]))
    drink.insert()

    return jsonify({'success': True, 'drinks': [drink.long()]})


@app.route('/drinks/<int:id>', methods = ['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if drink is None:
        abort(404)
    
    body = request.get_json()
    title = body.get('title', None)
    recipe = body.get('recipe', None)
    if title is None and recipe is None:
        abort(422)

    drink.title = title if title is not None else drink.title
    drink.recipe = recipe if recipe is not None else drink.recipe
    drink.update()

    return jsonify({'success': True, 'drinks': [drink.long()]})


@app.route('/drinks/<int:id>', methods = ['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if drink is None:
        abort(404)
    
    drink.delete()

    return jsonify({'success': True, 'delete': id})


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "Resource not found"}),
        404,
    )


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400, "message": "Bad request"}), 400


@app.errorhandler(500)
def bad_request(error):
    return jsonify({"success": False, "error": 500, "message": "Internal server error"}), 500


@app.errorhandler(401)
def unathorized(error):
    return jsonify({"success": False, "error": 401, "message": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({"success": False, "error": 403, "message": "Forbidden"}), 403


@app.errorhandler(AuthError)
def auth_error(error):
    return (
        jsonify({"success": False, "error": error.error, "message": error.error['description']}),
        error.status_code
    )

