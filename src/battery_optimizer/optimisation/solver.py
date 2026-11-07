from abc import ABC
from abc import abstractmethod


class Solver(ABC):

    @abstractmethod
    def solve(self):
        pass