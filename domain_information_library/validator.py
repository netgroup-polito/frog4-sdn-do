"""
Created on Feb 3, 2016

@author: gabrielecastellano

"""

import logging

from jsonschema import ValidationError

from exception import DomainInfoValidationError


class ValidateDomainInfo(object):

    def validate(self, domain_info):
        try:
            # TODO implement json validation against YANG model
            pass
        except ValidationError as err:
            logging.info(err.message)
            raise DomainInfoValidationError(err.message)

