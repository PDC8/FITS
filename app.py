"""
Application to run flask and endpoints
"""
import urllib.request
import urllib.error

from flask import Flask, render_template, request, make_response
from markupsafe import escape

from database import get_from_table, init_all_default_values
from default_values import default_tables


app = Flask(__name__)

# init_all_default_values(default_tables)
# get_from_table("Sizes")
