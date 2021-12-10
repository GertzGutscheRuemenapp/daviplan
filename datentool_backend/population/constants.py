from typing import List
from .models import AgeGroup

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
        return f'{self.to_age} bis unter {self.to_age + 1}'

    @property
    def code(self):
        def age_to_str(age: int, length: int = 2):
            return str(age).rjust(length, '0')
        if self.to_age >= self.INF:
            return f'ALT{age_to_str(self.from_age, length=3)}UM'
        return f'ALT{age_to_str(self.from_age, length=3)}B{age_to_str(self.to_age + 1)}'


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

    def check_agegroups(self, agegroups: List[AgeGroup]):
        """check if the agegroups are compatible to the regionalstatistik"""
        if len(agegroups) != len(self.agegroups):
            return False
        for i, agegroup in enumerate(agegroups):
            regstat_agegroup = self.agegroups[i]
            if age_group.from_age != regstat_agegroup.from_age:
                return False
            if age_group.to_age != regstat_agegroup.to_age:
                return False
        return True