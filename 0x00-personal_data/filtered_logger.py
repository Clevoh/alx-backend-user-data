#!/usr/bin/env python3
"""Handles user personal data
"""
import logging
import mysql.connector
from os import environ
import re
from typing import List


PII_FIELDS = ('name', 'email', 'phone', 'ssn', 'password')


def filter_datum(fields: List[str], redaction: str,
                 message: str, separator: str) -> str:
    """filter_datum that returns the log message obfuscated
    Args
        fields: list of field names to obfuscate
        separator: a character that separates the field and the log message
        redaction: a string representing the field lines to replace
        message: log message representing fields to obfuscate
    Return (str): log message obfuscated
    """
    for field in fields:
        message = re.sub(f'{field}=.*?{separator}',
                         f'{field}={redaction}{separator}', message)
    return message


class RedactingFormatter(logging.Formatter):
    """ Redacting Formatter class
        """

    REDACTION = "***"
    FORMAT = "[HOLBERTON] %(name)s %(levelname)s %(asctime)-15s: %(message)s"
    SEPARATOR = ";"

    def __init__(self, fields: List[str]):
        super(RedactingFormatter, self).__init__(self.FORMAT)
        self.fields = fields

    def format(self, record: logging.LogRecord) -> str:
        """ Filters values in incoming log records using filter_datum """
        record.msg = filter_datum(self.fields, self.REDACTION,
                                  record.getMessage(), self.SEPARATOR)
        return super(RedactingFormatter, self).format(record)


def get_logger() -> logging.Logger:
    """Create a logger for user data
    """
    logger = logging.getLogger("user_data")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(RedactingFormatter(list(PII_FIELDS)))
    logger.addHandler(stream_handler)

    return logger


def get_db() -> mysql.connector.connection.MySQLConnection:
    """ Get a connector to a database
    """
    host = environ.get('PERSONAL_DATA_DB_HOST')
    user = environ.get('PERSONAL_DATA_DB_USERNAME')
    password = environ.get('PERSONAL_DATA_DB_PASSWORD')
    db = environ.get('PERSONAL_DATA_DB_NAME')

    cur = mysql.connector.connection.MySQLConnection(
          host=host, user=user, password=password, database=db)

    return cur


def main():
    """Read and filter data
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users;")
    field_names = [desc[0] for desc in cursor.description]

    logger = get_logger()

    for row in cursor:
        str_row = ''.join(f'{f}={str(f)}; ' for r, f in zip(row, field_names))
        logger.info(str_row.strip())

    cursor.close()
    db.close()


if __name__ == '__main__':
    main()
