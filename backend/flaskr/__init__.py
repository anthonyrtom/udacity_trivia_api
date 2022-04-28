import os
from urllib import response
from click import Abort
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy import true

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the
    sample route after completing the TODOs
    """
    # CORS(app)
    CORS(app, resources={'/': {'origins': '*'}})

    # Helper method to paginate responses
    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]
        return current_questions

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.type).all()
        if len(categories) == 0:
            abort(404)
        return jsonify({'success': True, 'categories': {
                       category.id: category.type for category in categories}})

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom
    of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        try:
            all_questions = Question.query.all()
            total = len(all_questions)
            if total == 0:
                abort(404)
            all_questions = paginate_questions(request, all_questions)

            categories = Category.query.all()

            return jsonify({
                'questions': all_questions,
                'totalQuestions': total,
                'categories': {category.id: category.type for
                               category in categories},
                'currentCategory': None,
                'success': True
            })
        except BaseException:
            abort(400)

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the
    question will be removed.
    This removal will persist in the database and when you
    refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter(Question.id == id).one_or_none()
            if question is None:  # abort if question not found
                abort(404)
            question.delete()
            return jsonify({
                'success': True,
                'deleted': id
            })
        except BaseException:
            abort(422)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at
    the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def post_question():
        try:
            body = request.get_json()
            # test to see if the body has question, answer , category and
            # difficulty
            complete = (
                'question' in body) and (
                'answer' in body) and (
                'difficulty' in body) and (
                'category' in body)

            if complete:
                question = body.get('question')
                answer = body.get('answer')
                difficulty = body.get('difficulty')
                category = body.get('category')
                question = Question(question, answer, category, difficulty)
                question.insert()
                selection = Question.query.order_by(Question.id).all()
                current_question = paginate_questions(request, selection)
                return jsonify({
                    'success': True,
                    'created': question.id
                })
            else:
                abort(400)
        except BaseException:
            abort(422)
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()
        try:
            search_term = body.get('searchTerm', None)
            if search_term:
                search_result = Question.query.filter(
                    Question.question.ilike(f'%{search_term}%')).all()
                paginated_questions = paginate_questions(
                    request, search_result)
                if len(search_result) > 0:
                    return jsonify({
                        'questions': paginated_questions,
                        'totalQuestions': len(search_result),
                        'currentCategory': None
                    })
                else:
                    return jsonify({
                        'questions': [],
                        'totalQuestions': 0,
                        'currentCategory': None})
            else:
                abort(400)
        except BaseException:
            abort(422)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):
        try:
            selection = Question.query.filter(
                Question.category == str(id)).all()
            paginated = paginate_questions(request, selection)
            category = Category.query.filter(Category.id == id).one_or_none()
            return jsonify({
                'success': True,
                'questions': paginated,
                'totaQuestions': len(selection),
                'currentCategory': category.type
            })
        except BaseException:
            abort(404)
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    def get_random_question(prev_questions, category="click"):
        """a helper function to get a random question from a category"""
        counter = 0
        all_questions = []
        curr_question = {}
        if category['type'] == "click":
            all_questions = Question.query.all()
        else:
            filtered_category = Category.query.filter(
                Category.type == str(category['type'])).one_or_none()
            category_id = filtered_category.id
            all_questions = Question.query.filter(
                Question.category == str(category_id)).all()
        for i in range(len(all_questions)):
            question = random.choice(all_questions)
            if not str(question.id) in prev_questions:
                curr_question = question.format()
                break
        return curr_question

    @app.route('/quizzes', methods=['POST'])
    def get_quiz():
        try:
            body = request.get_json()
            category = body.get('quiz_category', None)
            previous_questions = body.get('previous_questions', None)
            if not('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            question = get_random_question(previous_questions, category)
            return jsonify({
                'questions': question,
                'success': True})

        except BaseException:
            abort(404)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (jsonify({"success": False, "error": 404,
                         "message": "resource not found"}), 404, )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                     "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400,
                       "message": "bad request"}), 400

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"success": False, "error": 500,
                       "message": "internal server error"}), 500

    return app
