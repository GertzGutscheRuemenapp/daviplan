from typing import List, Union
import pandas as pd
from datentool_backend.demand.models import AgeGroup


class RegStatAgeGroup:
    """Agegroup of Regionalstatistik"""
    INF = 999

    def __init__(self,
                 from_age: int,
                 to_age: int):
        self.from_age = from_age
        self.to_age = to_age

    @property
    def name(self):
        if self.from_age == 0:
            return f'unter {self.to_age + 1} Jahre'
        if self.to_age >= self.INF:
            return f'{self.from_age} Jahre und mehr'
        return f'{self.from_age} bis unter {self.to_age + 1}'

    @property
    def code(self):
        def age_to_str(age: int, length: int = 2):
            return str(age).rjust(length, '0')
        if self.to_age >= self.INF:
            return f'ALT{age_to_str(self.from_age, length=3)}UM'
        return (f'ALT{age_to_str(self.from_age, length=3)}'
                f'B{age_to_str(self.to_age + 1)}')

    def __eq__(self, other: Union['RegStatAgeGroup', AgeGroup]) -> bool:
        # if other age surpasses custom "infinite" value
        # take the "infinite" value
        to_age = other.to_age if other.to_age <= self.INF else self.INF
        return self.from_age == other.from_age and self.to_age == to_age

    def __ne__(self, other: Union['RegStatAgeGroup', AgeGroup]) -> bool:
        return not self == other

    def __repr__(self) -> str:
        return self.code

    def __str__(self) -> str:
        return self.name


class RegStatAgeGroups:
    """Agegroups of Regionalstatistik"""
    agegroups = [
        RegStatAgeGroup(0, 2),
        RegStatAgeGroup(3, 5),
        RegStatAgeGroup(6, 9),
        RegStatAgeGroup(10, 14),
        RegStatAgeGroup(15, 17),
        RegStatAgeGroup(18, 19),
        RegStatAgeGroup(20, 24),
        RegStatAgeGroup(25, 29),
        RegStatAgeGroup(30, 34),
        RegStatAgeGroup(35, 39),
        RegStatAgeGroup(40, 44),
        RegStatAgeGroup(45, 49),
        RegStatAgeGroup(50, 54),
        RegStatAgeGroup(55, 59),
        RegStatAgeGroup(60, 64),
        RegStatAgeGroup(65, 74),
        RegStatAgeGroup(75, RegStatAgeGroup.INF)
    ]

    @classmethod
    def check(cls, agegroups: List[AgeGroup]) -> bool:
        """
        check if the agegroups are compatible to the regionalstatistik
        in any order
        """
        if len(agegroups) != len(cls.agegroups):
            return False
        for agegroup in agegroups:
            found = False
            for regstat_agegroup in cls.agegroups:
                if regstat_agegroup == agegroup:
                    found = True
                    break
            if not found:
                return False
        return True

    @classmethod
    def get(cls, code: str) -> RegStatAgeGroup:
        for ag in cls.agegroups:
            if ag.code == code:
                return ag
        return None

    @classmethod
    def as_series(cls) -> pd.Series:
        """return as pandas.Series"""
        return pd.Series(range(1, 18),
                         index=[repr(ag) for ag in cls.agegroups],
                         name='age_group_id')


regstatgenders = pd.Series([1, 2],
                           index=['GESM', 'GESW'],
                           name='gender_id')
