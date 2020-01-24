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

class Articles_All_WF(Resource):
  def get(self):
    articles = get_from_db.get_allarticles_word_freq()
    return articles

class Articles_Publisher(Resource):
  def get(self, publisher):
    articles = get_from_db.get_pub_articles(publisher)
    return articles

class Articles_Publisher_WF(Resource):
  def get(self, publisher):
    articles = get_from_db.get_pub_articles_word_freq(publisher)
    return articles

class Article_Publisher(Resource):
  def get(self, pub, slug):
    article = get_from_db.get_article_by_pub_slug(pub, slug, [])
    return article

class Article(Resource):
  def get(self, slug):
    article = get_from_db.get_article_by_slug(slug, [])
    return article

class Articles_Random(Resource):
  def get(self):
    article = get_from_db.get_random_article()
    return article

class Articles_Progress(Resource):
  def get(self):
    articles = get_from_db.get_match_progress()
    return articles

class Articles_Publisher_Matched(Resource):
  def get(self, publisher):
    articles = get_from_db.get_publisher_matched(publisher)
    return articles

class Articles_Publisher_Unmatched(Resource):
  def get(self, publisher):
    articles = get_from_db.get_publisher_unmatched(publisher)
    return articles

class Articles_All_Matched(Resource):
  def get(self):
    articles = get_from_db.get_articles_all_matches()
    return articles

class Ask(Resource):
  # js object = {
  #   article_slug: '',
  #   article_publisher: '',
  #   tokens: {
  #     title: Boolean,
  #     author: Boolean,
  #     tags: Boolean,
  #     body: Boolean
  #   },
  #   size: integer
  # }

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('article_slug', type=str)
    parser.add_argument('article_publisher', type=str)
    parser.add_argument('tokens', type=dict)
    parser.add_argument('size', type=inputs.natural)
    data = parser.parse_args()
    result = ask.ask(data.article_slug, data.article_publisher, data.tokens, data.size)
    return result


class Send(Resource):
  # js object = {
  #   inputs_slug: '',
  #   inputs_publisher: '',
  #   match_slug: '',
  #   match_publisher: '',
  #   score: integer,
  #   timestamp: new Date().toISOString()
  # }

  def post(self):
    parser = reqparse.RequestParser()
    parser.add_argument('input_slug', type=str)
    parser.add_argument('input_publisher', type=str)
    parser.add_argument('match_slug', type=str)
    parser.add_argument('match_publisher', type=str)
    parser.add_argument('score', type=inputs.natural)
    parser.add_argument('timestamp', type=inputs.datetime_from_iso8601)
    feedback = parser.parse_args()
    response = save_to_db.feedback(feedback)
    return response


api.add_resource(Articles_All, '/api/articles')
api.add_resource(Articles_All_WF, '/api/articles-wf')
api.add_resource(Articles_Publisher, '/api/articles/<string:publisher>')
api.add_resource(Article_Publisher, '/api/articles/<string:pub>/<string:slug>')
api.add_resource(Articles_Publisher_WF, '/api/articles-wf/<string:publisher>')
api.add_resource(Article, '/api/article/<string:slug>')
api.add_resource(Articles_Random, '/api/article/random')
api.add_resource(Articles_Progress, '/api/articles/progress')
api.add_resource(Articles_All_Matched, '/api/articles/all/matched')
api.add_resource(Articles_Publisher_Matched, '/api/articles/<string:publisher>/matched')
api.add_resource(Articles_Publisher_Unmatched, '/api/articles/<string:publisher>/unmatched')
api.add_resource(Ask, '/api/ask')
api.add_resource(Send, '/api/send')

if __name__ == '__main__':
  app.run()
