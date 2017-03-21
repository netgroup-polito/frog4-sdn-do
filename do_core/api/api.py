"""
Created on Mar 20, 2016

@author: gabrielecastellano
"""

from flask import Blueprint
from flask_restplus import Api

root_blueprint = Blueprint('root', __name__)
api = Api(root_blueprint, version='1.0', title='SDN Domain Orchestrator API', description='SDN Domain Orchestrator API',
          doc='/api_docs')
