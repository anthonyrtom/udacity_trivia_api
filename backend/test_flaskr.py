import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia"
        self.database_path = "postgresql://{}:{}@{}/{}".format('postgres','pass123' ,'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)
        #a sample question for use in tests
        self.new_question = {
            'question': 'Which is one of the original 7 wonders of the world found in Zimbabwe',
            'answer': 'Victoria Falls',
            'difficulty': 3,
            'category': 4
        }
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    #Test get questions for success
    def test_get_questions(self):
        response = self.client().get('/questions')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['totalQuestions']) # test count of questions working
        self.assertTrue(len(data['questions'])) #test there is atleast one question
    
    #test for a resource not there on questions
    def test_404_questions_not_found(self):
        response = self.client().get('/questions/?page=1000')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found') 
        

    #test get categories
    def test_get_categories(self):
        response = self.client().get('/categories')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))

    #test non existant categories
    def test_404_categories(self):
        response = self.client().get('/categories/500')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')   
    
    # test seraching a question {successful one}
    def test_search_question(self):
        response = self.client().post('/questions/search', json={'searchTerm':'Taj'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["totalQuestions"])
        self.assertTrue(len(data['questions']))
    
    #search for non existant terms
    def test_404_search_question_no_success(self):
        response = self.client().post('/questions/search', json={'searchTerm':'fizzbuzz'})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["error"], 404)
        self.assertEqual(data["message"], "resource not found")

    #test creating a question
    def test_create_question(self):
        counter_before_addition = len(Question.query.all()) #get no. of questions before adding one
        response = self.client().post('/questions', json=self.new_question)
        data = json.loads(response.data)
        counter_after_addition = len(Question.query.all())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertGreater(counter_after_addition, counter_before_addition)

    #test a failure of question creation
    def test_422_create_question(self):
        counter_before_addition = len(Question.query.all()) #get no. of questions before adding one
        response = self.client().post('/questions', json={})
        data = json.loads(response.data)
        counter_after_addition = len(Question.query.all())
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(counter_after_addition, counter_before_addition)
    
    #test get questions by category success
    def test_get_qn_by_category(self):
        response = self.client().get('categories/5/questions')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertGreater(len(data['questions']), 0)
        self.assertEqual(data['currentCategory'], 'Entertainment') #check category that it is 4 in our case
    
    #test get questions by category unsuccssful category
    def test_404_category_not_found(self):
        response = self.client().get('categories/1001/questions')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['error'], 404)
        self.assertEqual(data['message'], 'resource not found')
    
    #test successful quizz request
    def test_get_quizz(self):
        response = self.client().post('/quizzes', json={"previous_questions": [2, 3], "quiz_category":"Geography"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
    
    #test unsuccessful get quizzes request
    def test_404_unsuccessful_quizzes(self):
        response = self.client().post('quizzes', json={"previous_questions": [2, 3], "quiz_category":"ancient"})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertRaises(KeyError, lambda: data['questions'])
        self.assertEqual(data['message'], 'resource not found')
        self.assertEqual(data['error'], 404)
    
    #test delete question
    def test_delete_question(self):
        #first create a new question
        question = Question(self.new_question['question'], self.new_question['answer'], self.new_question['category'], self.new_question['difficulty'])
        question.insert()
        question_id = question.id #get question ID
        response = self.client().delete('questions/{}'.format(question_id))
        data = json.loads(response.data)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)

    #test for an unsuccessful deletion
    def test_404_unsuccesful_deletion(self):
        response = self.client().delete('questions/1200')
        data = json.loads(response.data)
        self.assertEqual(data['success'], False)
        self.assertRaises(KeyError, lambda: data['deleted'])
        self.assertEqual(data['message'], 'unprocessable')
        self.assertEqual(data['error'], 422)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()