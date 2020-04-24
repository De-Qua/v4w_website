from flask import Flask
from config import Config
import sys
import os

app = Flask(__name__)
app.config.from_object(Config)

from app import routes, errors
