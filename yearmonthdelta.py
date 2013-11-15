# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

__author__ = "Ilja Everilä"
__copyright__ = "Copyright (C) 2013 Ilja Everilä"
__version__ = "0.1"
__docformat__ = "epytext"
__doc__ = """Simple year and month delta for python datetime.date and
datetime.datetime types.

By default impossible results are rounded to the nearest sensible
result. Mainly this means that results with day of month values higher than the
largest possible day of the resulting month will be rounded down to the largest
possible day of month. For example::

    >>> datetime.date(2000, 3, 31) - yearmonthdelta(0, 1)
    datetime.date(2000, 2, 29)

"""

import calendar
import datetime
import functools

@functools.total_ordering
class yearmonthdelta(object):
    """Year and month deltas for dates and datetimes.

    Instances should lazily normalize values.
    >>> ymd = yearmonthdelta(1, -13)
    >>> ymd.years, ymd.months, str(ymd)
    (1, -13, '0 years -1 month')

    Addition with other deltas does not normalize.
    >>> ymd = yearmonthdelta(2, 1) + yearmonthdelta(1, -5)
    >>> ymd.years, ymd.months, str(ymd)
    (3, -4, '2 years 8 months')

    Rich ordering operations.
    >>> yearmonthdelta(1, 0) > yearmonthdelta(0, 12)
    False
    >>> yearmonthdelta(1, 0) > yearmonthdelta(0, 11)
    True
    >>> yearmonthdelta(1, 0) >= yearmonthdelta(0, 12)
    True
    >>> yearmonthdelta(1, 0) >= yearmonthdelta(0, 13)
    False
    >>> yearmonthdelta(1, 0) <= yearmonthdelta(0, 12)
    True
    >>> yearmonthdelta(1, 0) <= yearmonthdelta(0, 11)
    False

    Comparing with unsupported types should raise an error.
    >>> yearmonthdelta(1, 11) > 1
    Traceback (most recent call last):
        ...
    TypeError: can't compare yearmonthdelta to int

    Default operation rounds impossible day values to nearest sensible value.
    >>> datetime.datetime(2013, 3, 31) + yearmonthdelta(0, -1)
    datetime.datetime(2013, 2, 28, 0, 0)

    Leap years with rounding should produce no errors.
    >>> datetime.datetime(2004, 2, 29) - yearmonthdelta(1, 0)
    datetime.datetime(2003, 2, 28, 0, 0)
    >>> datetime.datetime(2004, 2, 29) - yearmonthdelta(4, 0)
    datetime.datetime(2000, 2, 29, 0, 0)

    Rounding can be prevented in order to catch errors when impossible
    dates are produced.
    >>> print(datetime.datetime(2013, 3, 31) + yearmonthdelta(0, -1, False))
    Traceback (most recent call last):
        ...
    ValueError: day is out of range for month
    >>> ymd = datetime.datetime(2004, 2, 29)
    >>> print(ymd - yearmonthdelta(1, 0, False))
    Traceback (most recent call last):
        ...
    ValueError: day is out of range for month

    When adding two deltas stricter rounding setting is honoured.
    >>> ymd = yearmonthdelta(1, 0) + yearmonthdelta(1, 0, False)
    >>> ymd.rounding
    False
    """

    def __init__(self, years=0, months=0, rounding=True):
        """
        >>> yearmonthdelta()
        yearmonthdelta.yearmonthdelta(0, 0, True)
        >>> yearmonthdelta(1)
        yearmonthdelta.yearmonthdelta(1, 0, True)
        >>> yearmonthdelta(1, 1)
        yearmonthdelta.yearmonthdelta(1, 1, True)
        >>> yearmonthdelta(1, 1, False)
        yearmonthdelta.yearmonthdelta(1, 1, False)
        """
        self.years = years
        self.months = months
        self.rounding = bool(rounding)

    @staticmethod
    def _normalize(years, months):
        """
        >>> yearmonthdelta._normalize(2000, 25)
        (2002, 1)
        >>> yearmonthdelta._normalize(1, -25)
        (-1, -1)
        """
        total = years * 12 + months

        if total == 0:
            return 0, 0

        # NOTE: evil variable reuse
        years, months = divmod(abs(total) - 1, 12)
        months += 1

        if total < 0:
            # swap sign as original delta is negative
            years, months = -years, -months

        return years, months

    def _add_datetime(self, dt):
        day = dt.day
        year, month = self._normalize(dt.year + self.years,
                                      dt.month + self.months)

        if self.rounding:
            day = min(day, calendar.monthrange(year, month)[1])

        return dt.replace(year, month, day)

    def __add__(self, other):
        """
        Adding an integer adds months.
        >>> ymd = yearmonthdelta(1, 11) + 2
        >>> ymd.years, ymd.months, str(ymd)
        (1, 13, '2 years 1 month')

        Adding an unsupported type should return NotImplemented
        >>> yearmonthdelta(1, 11) + '1'
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for +: 'yearmonthdelta' and 'str'
        """
        if isinstance(other, (datetime.date, datetime.datetime)):
            return self._add_datetime(other)

        elif isinstance(other, yearmonthdelta):
            return yearmonthdelta(self.years + other.years,
                                  self.months + other.months,
                                  self.rounding and other.rounding)

        elif isinstance(other, (int, long)):
            return yearmonthdelta(self.years,
                                  self.months + other,
                                  self.rounding)

        return NotImplemented

    def __radd__(self, other):
        """
        Right add with datetime and date should work.
        >>> yearmonthdelta(0, 1) + datetime.date(2000, 1, 1)
        datetime.date(2000, 2, 1)

        Adding to an unsupported type should raise an error
        >>> 1 + yearmonthdelta(0, 1)
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for +: 'int' and 'yearmonthdelta'
        """
        if isinstance(other, (datetime.date, datetime.datetime)):
            return self._add_datetime(other)

        raise TypeError("unsupported operand type(s) for +: '{}' and '{}'"
                        .format(type(other).__name__,
                                yearmonthdelta.__name__))

    def __pos__(self):
        """
        Returns a yearmonthdelta object with the same value.
        >>> ymd1 = yearmonthdelta(1, 1)
        >>> ymd2 = +ymd1
        >>> ymd1 is ymd2
        False
        """
        return yearmonthdelta(self.years, self.months, self.rounding)

    def __neg__(self):
        """
        Returns a yearmonthdelta object with sign swapped.
        >>> ymd1 = yearmonthdelta(1, -13)
        >>> ymd2 = -ymd1
        >>> ymd1 is ymd2
        False
        >>> ymd2.years, ymd2.months, str(ymd2)
        (-1, 13, '0 years 1 month')
        """
        return yearmonthdelta(-self.years, -self.months, self.rounding)

    def __sub__(self, other):
        """
        Subtracting an unsupported type should return NotImplemented.
        >>> yearmonthdelta(1, 11) - 1.0
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for -: 'yearmonthdelta' and 'float'
        """
        return self.__add__(-other)

    def __rsub__(self, other):
        """
        Subtracting from an unsupported type should raise an error.
        >>> 1 - yearmonthdelta(0, 1)
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for -: 'int' and 'yearmonthdelta'
        """
        if isinstance(other, (datetime.date, datetime.datetime)):
            return (-self)._add_datetime(other)

        raise TypeError("unsupported operand type(s) for -: '{}' and '{}'"
                        .format(type(other).__name__,
                                yearmonthdelta.__name__))

    def __mul__(self, other):
        """
        >>> yearmonthdelta(2, 1) * 3
        yearmonthdelta.yearmonthdelta(6, 3, True)
        >>> yearmonthdelta(2, -1) * -1
        yearmonthdelta.yearmonthdelta(-2, 1, True)
        >>> yearmonthdelta(2, 1).__mul__('no go')
        NotImplemented
        >>> yearmonthdelta(2, 1) * 2.0
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for *: 'yearmonthdelta' and 'float'
        """
        if isinstance(other, (int, long)):
            return yearmonthdelta(self.years * other,
                                  self.months * other,
                                  self.rounding)

        return NotImplemented

    def __rmul__(self, other):
        """
        >>> 3 * yearmonthdelta(2, 1)
        yearmonthdelta.yearmonthdelta(6, 3, True)
        >>> -1 * yearmonthdelta(2, -1)
        yearmonthdelta.yearmonthdelta(-2, 1, True)
        >>> 2.0 * yearmonthdelta(2, 1)
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for *: 'float' and 'yearmonthdelta'
        """
        product = self.__mul__(other)

        if product is NotImplemented:
            raise TypeError("unsupported operand type(s) for *: '{}' and '{}'"
                            .format(type(other).__name__,
                                    yearmonthdelta.__name__))

        return product

    @property
    def _total_months(self):
        return self.years * 12 + self.months

    def __lt__(self, other):
        """
        >>> yearmonthdelta(1, 0) < yearmonthdelta(0, 12)
        False
        >>> yearmonthdelta(1, 0) < yearmonthdelta(0, 13)
        True
        """
        if isinstance(other, yearmonthdelta):
            return self._total_months < other._total_months

        raise TypeError("can't compare {} to {}".format(
            yearmonthdelta.__name__, type(other).__name__))

    def __eq__(self, other):
        """
        >>> yearmonthdelta(1, 0) == yearmonthdelta(0, 12)
        True
        >>> yearmonthdelta(1, 0) == yearmonthdelta(0, 13)
        False
        """
        if isinstance(other, yearmonthdelta):
            return self._total_months == other._total_months

        raise TypeError("can't compare {} to {}".format(
            yearmonthdelta.__name__, type(other).__name__))

    def __ne__(self, other):
        """
        >>> yearmonthdelta(1, 0) != yearmonthdelta(0, 12)
        False
        >>> yearmonthdelta(1, 0) != yearmonthdelta(0, 13)
        True
        """
        return not self.__eq__(other)

    @staticmethod
    def _ngettext(singular, plural, count):
        return singular if abs(count) == 1 else plural

    def __str__(self):
        years, months = self._normalize(self.years, self.months)
        return "{} {} {} {}".format(
            years,
            self._ngettext("year", "years", years),
            months,
            self._ngettext("month", "months", months))

    def __repr__(self):
        return "{}.{}({}, {}, {})".format(
            yearmonthdelta.__module__,
            yearmonthdelta.__name__,
            repr(self.years),
            repr(self.months),
            repr(self.rounding))
