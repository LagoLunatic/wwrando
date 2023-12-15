from dataclasses import fields, MISSING, Field, _recursive_repr, _FIELDS, _FIELD, asdict
from typing import Any, Type

class Option(Field):
  type: Type
  
  __slots__ = Field.__slots__ + (
    'description', 'choice_descriptions',
    'minimum', 'maximum',
    'permalink', 'hidden', 'unbeatable',
  )
  
  def __init__(self, default, default_factory,
               description: str, choice_descriptions: dict[Any, str],
               minimum, maximum,
               permalink: bool, hidden: bool, unbeatable: bool):
    super().__init__(default, default_factory, init=True, repr=True,
                     hash=None, compare=True, metadata=None, kw_only=True)
    self.description = description
    self.choice_descriptions = choice_descriptions
    self.minimum = minimum
    self.maximum = maximum
    self.permalink = permalink
    self.hidden = hidden
    self.unbeatable = unbeatable
  
  @_recursive_repr
  def __repr__(self):
      return ('Option('
              f'name={self.name!r},'
              f'type={self.type!r},'
              f'default={self.default!r},'
              f'default_factory={self.default_factory!r}'
              ')')

def option(default=MISSING, default_factory=MISSING,
           description="", choice_descriptions={},
           minimum=None, maximum=None,
           permalink=True, hidden=False, unbeatable=False):
  if default is MISSING and default_factory is MISSING:
    raise ValueError('must specify either default or default_factory')
  return Option(
    default, default_factory,
    description, choice_descriptions,
    minimum, maximum,
    permalink, hidden, unbeatable
  )

class BaseOptions:
  @classmethod
  @property
  def all(cls) -> tuple[Option, ...]:
    return fields(cls)
  
  @classmethod
  @property
  def named(cls) -> dict[str, Option]:
    return {
      name: field
      for name, field in getattr(cls, _FIELDS).items()
      if field._field_type is _FIELD
    }
  
  dict = asdict
  
  def __getitem__(self, option_name) -> Option:
    fields = getattr(self, _FIELDS)
    field = fields[option_name]
    if field._field_type is not _FIELD:
      raise KeyError(option_name)
    return getattr(self, option_name)
