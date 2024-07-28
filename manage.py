#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    try:
        from django.core.management import execute_from_command_line
        from django.conf import settings

        if 'test' in sys.argv:
            import logging
            logging.disable(logging.CRITICAL)
            settings.DEBUG = False
            settings.PASSWORD_HASHERS = [
                'django.contrib.auth.hashers.MD5PasswordHasher',
            ]

        if 'test' in sys.argv and '--time' in sys.argv:
            sys.argv.remove('--time')
            from django import test
            import time

            def setUp(self):
                self.startTime = time.time()

            def tearDown(self):
                total = time.time() - self.startTime
                if total > 0.5:
                    print("nt033[91m%.3fst%s033[0m" % ( \
                        total, self._testMethodName))
                
            test.TestCase.setUp = setUp
            test.TestCase.tearDown = tearDown


    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
