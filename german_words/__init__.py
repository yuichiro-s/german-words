from flask import Flask

app = Flask(__name__)

from german_words import views
