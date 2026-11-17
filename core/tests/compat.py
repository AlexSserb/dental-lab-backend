"""Compatibility shims for the local test environment (not needed under the docker image's Python 3.13)."""
from django.template import context


def _base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate


context.BaseContext.__copy__ = _base_context_copy
