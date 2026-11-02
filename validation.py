"""Shared dataclass field contract for catalogs, snapshots and sync."""
from dataclasses import MISSING, fields
from typing import get_args, get_origin, get_type_hints


def matches(value, annotation):
    origin = get_origin(annotation)
    if origin is list:
        return isinstance(value, list) and all(matches(x, get_args(annotation)[0]) for x in value)
    if origin is dict:
        args = get_args(annotation)
        return isinstance(value, dict) and (not args or all(
            matches(k, args[0]) and matches(v, args[1]) for k, v in value.items()))
    return isinstance(value, annotation)


def validate_model(data, model):
    if not isinstance(data, dict):
        raise ValueError(f'{model.__name__} must be an object.')
    hints = get_type_hints(model)
    valid = {field.name for field in fields(model)}
    if data.keys() - valid:
        raise ValueError(f'Unknown {model.__name__} fields: {sorted(data.keys() - valid)}')
    for field in fields(model):
        if field.name not in data:
            if field.default is MISSING and field.default_factory is MISSING:
                raise ValueError(f'{model.__name__}.{field.name} is required.')
        elif not matches(data[field.name], hints[field.name]):
            raise ValueError(f'{model.__name__}.{field.name} has an invalid type.')
