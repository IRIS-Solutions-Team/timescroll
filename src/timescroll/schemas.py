r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import namedtuple, Counter

# Typing imports
from typing import Any, Callable, Iterable, NoReturn

#]


__all__ = (
    "Schema",
    "EmptySchema",
)


def _validate_unique_fields(field_names: Iterable[str], ) -> None:
    r"""
    Make sure field names are unique, and raise ValueError if not
    """
    field_counts = Counter(field_names, )
    duplicates = [name for name, count, in field_counts.items() if count > 1]
    if duplicates:
        raise ValueError(
            f"Duplicate field names found in metadata: {duplicates}"
        )


class _Validator:
    r"""
    """
    #[
    def validate(self, *args, **kwargs,) -> bool:
        r"""
        """
        ...

    def __call__(self, *args, **kwargs, ) -> bool:
        r"""
        """
        return self.validate(*args, **kwargs,)
    #]


class _FreeFormValidator(_Validator, ):
    r"""
    """
    #[
    def __init__(self,) -> None:
        r"""
        """
        pass

    def validate(self, value: Any,) -> bool:
        r"""
        """
        return True
    #]


class _ValueValidator(_Validator, ):
    r"""
    """
    #[
    def __init__(
        self,
        allowed_value: Any,
    ) -> None:
        r"""
        """
        self.allowed_value = allowed_value

    def validate(self, value: Any,) -> bool:
        r"""
        """
        return value == self.allowed_value
    #]


class _EnumerationValidator(_Validator, ):
    r"""
    """
    #[
    def __init__(
        self,
        allowed_values: Iterable[Any],
    ) -> None:
        r"""
        """
        self.allowed_values = frozenset(allowed_values)

    def validate(self, value: Any,) -> bool:
        r"""
        """
        return value in self.allowed_values
    #]


class _TestValidator(_Validator, ):
    r"""
    """
    #[
    def __init__(
        self,
        test_func: Callable[[Any], bool],
    ) -> None:
        r"""
        """
        self.test_func = test_func

    def validate(self, value: Any,) -> bool:
        r"""
        """
        return self.test_func(value)
    #]


_VALIDATION_DISPATCH = {
    None: _FreeFormValidator,
    "value": _ValueValidator,
    "enumeration": _EnumerationValidator,
    "test": _TestValidator,
}


class Schema:
    r"""
    """
    #[

    def __init__(
        self,
        **kwargs,
    ) -> None:
        r"""
        """
        fields = tuple(kwargs.keys(), )
        _validate_unique_fields(fields, )
        self.fields = fields
        self._validators = {}
        for field_name, validator_specs in kwargs.items():
            self._validators[field_name] = _build_field_validator(validator_specs, )

    def iteratate_validator_results(
        self,
        data: namedtuple,
    ) -> Iterable[bool]:
        r"""
        """
        for i in self.fields:
            yield self._validators[i](getattr(data, i, ), )

    def validate(
        self,
        data: namedtuple,
    ) -> bool:
        r"""
        """
        return all(self.iteratate_validator_results(data, ))

    def validate_and_raise(
        self,
        data: namedtuple,
    ) -> None | NoReturn:
        r"""
        """
        invalid_fields = tuple(
            i for i, is_valid, in zip(
                self.fields,
                self.iteratate_validator_results(data, ),
            )
            if not is_valid
        )
        if invalid_fields:
            raise ValueError(
                f"Invalid metadata fields: {invalid_fields}"
            )


EmptySchema = Schema()


def _build_field_validator(validator_specs: Any, ) -> Any:
    r"""
    """
    #[
    if validator_specs is None:
        return _FreeFormValidator()
    validator_type = validator_specs[0]
    validator_parameter = (
        validator_specs[1] if len(validator_specs) > 1
        else None
    )
    return _VALIDATION_DISPATCH[validator_type](validator_parameter, )
    #]


