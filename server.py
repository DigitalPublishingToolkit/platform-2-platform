from flask import Flask
from flask_restful import Resource, Api, reqparse, inputs
import save_to_db
import get_from_db
import ask

app = Flask(__name__)
api = Api(app)

class Articles_All(Resource):
  def get(self):
    articles = get_from_db.get_allarticles()
    return articles

class Articles_Publisher(Resource):
  def get(self, publisher):
    articles = get_from_db.get_pub_articles(publisher)
    return articles

class Articles_Random(Resource):
  def get(self):
    articles = get_from_db.get_random_article()
    return articles

class Ask(Resource):
  # js object = {
  #   article_title: '',
  #   article_publisher: '',
  #   tokens: {
  #     title: Boolean,
  #     author: Boolean,
  #     tags: Boolean,
  #     body: Boolean
  #   }
  # }

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('article_title', type=str)
    parser.add_argument('article_publisher', type=str)
    parser.add_argument('article_id', type=inputs.natural)
    parser.add_argument('tokens', type=dict)
    data = parser.parse_args()
    result = ask.ask(data.article_title, data.article_publisher, data.article_id, data.tokens)
    return result


class Send(Resource):
  # js object = {
  #   inputs_title: '',
  #   inputs_publisher: '',
  #   match_title: '',
  #   match_publisher: '',
  #   score: integer,
  #   timestamp: new Date().toISOString()
  # }

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('input_title', type=str)
    parser.add_argument('input_publisher', type=str)
    parser.add_argument('match_title', type=str)
    parser.add_argument('match_publisher', type=str)
    parser.add_argument('score', type=inputs.natural)
    parser.add_argument('timestamp', type=inputs.datetime_from_iso8601)
    feedback = parser.parse_args()
    response = save_to_db.feedback(feedback)
    return response


api.add_resource(Articles_All, '/api/articles')
api.add_resource(Articles_Publisher, '/api/articles/<string:publisher>')
api.add_resource(Articles_Random, '/api/article/random')
api.add_resource(Ask, '/api/ask')
api.add_resource(Send, '/api/send')

if __name__ == '__main__':
  app.run()
