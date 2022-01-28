from CC2021.LLC.parser import Parser
from CC2021.strucs import TableSyntaticAnalyser, LLC, Production
from itertools import combinations
from utils.utils import *


class Proc:
    
    def __init__(self):
        self.llc: LLC = None
        self.empty_symbol = EMPTY_SYMBOL
        self.stack_bottom = STACK_BOTTOM

    def create_llc(self, llc1):
        self.llc: LLC = llc1

        first = {i: set() for i in self.llc.non_terminals}
        first.update((i, {i}) for i in self.llc.terminals)
        first[self.empty_symbol] = {self.empty_symbol}

        follow = {i: set() for i in self.llc.non_terminals}
        follow[self.empty_symbol] = {self.stack_bottom}
        follow[self.llc.start_s] = {self.stack_bottom}

        epsilon = {self.empty_symbol}

        while True:
            updated = False

            for prod in self.llc.prods:
                # Calculate FIRST
                for symbol in prod.body:
                    updated |= merge(first[prod.head], first[symbol])

                    if symbol not in epsilon:
                        break

                else:
                    first[prod.head] |= {self.empty_symbol}
                    updated |= merge(epsilon, {prod.head})

                # Calculate FOLLOW
                temp = follow[prod.head]
                for symbol in reversed(prod.body):
                    if symbol in follow:
                        updated |= merge(follow[symbol], temp)

                    if symbol in epsilon:
                        temp = temp.union(first[symbol])
                    else:
                        temp = first[symbol]

            if not updated:
                break
        self.firsts = first
        self.follows = follow

    def read_llc(self, path):
        p = Parser()
        self.create_llc(p.parse(path))


    def calculate_first_prod(self, body):
        first = set()
        for s in body:
            first_s = self.firsts[s]

            first |= self.firsts[s] - {self.empty_symbol}

            if self.empty_symbol not in first_s:
                break

        else:
            first |= {self.empty_symbol}

        return first

    # checking if LLC is LL(1)
    def ll_first_condition(self, p1: Production, p2: Production):
        # checks if
        # first(p1) <intersection> first(p2) == empty

        p1_first = self.calculate_first_prod(p1.body)
        p2_first = self.calculate_first_prod(p2.body)

        checks = (p1_first.intersection(p2_first) == set())

        if not checks:
            print('The LLC is not LL(1)!')
            print('--> Firsts of first production: %s' % p1_first)
            print('--> Firsts of second production: %s' % p2_first)

        return checks

    def ll_second_condition(self, p1: Production, p2: Production):
        # checks if
        # for A -> p1 | p2
        # if(p1 -*> &) then (first(p2) <intersection> follow(A) = empty)
        # if(p2 -*> &) then (first(p1) <intersection> follow(A) = empty)

        check = True
        follow_head = self.follows[p1.head]

        p1_first = self.calculate_first_prod(p1.body)
        p2_first = self.calculate_first_prod(p2.body)

        if EMPTY_SYMBOL in p2_first:
            check &= p1_first.intersection(follow_head) == set()

        if EMPTY_SYMBOL in p1_first:
            check &= p2_first.intersection(follow_head) == set()

        if not check:
            print('The LLC is not LL(1)!')
            print('First of p1 %s' % p1_first)
            print('First of p2 %s' % p2_first)
            print('follow of head of prods %s' % follow_head)

        return check

    def is_ll1(self):
        for nt in self.llc.non_terminals:
            if not self.check_conditions_on_productions_of(nt):
                return False
            return True

    def check_conditions_on_productions_of(self, nt):
        productions = list(filter(lambda k: k.head == nt, self.llc.prods))

        for p1, p2 in combinations(productions, 2):
            first_part_of_theorem = self.ll_first_condition(p1, p2)
            second_part_of_theorem = self.ll_second_condition(p1, p2)
            if not (first_part_of_theorem and second_part_of_theorem):
                print('|Grammar is not LL(1), as shown by productions')
                print('|    | P1: %s' % p1)
                print('|    | P2: %s' % p2)
                return False

        return True

    def create_table(self):
        if not self.is_ll1():
            print("Can't generate the syntatic analyser table for a non-LL(1) grammar")
            return False

        table = TableSyntaticAnalyser(self.llc.terminals, self.llc.non_terminals)

        for prod in self.llc.prods:
            first_body = self.calculate_first_prod(prod.body)

            for t in first_body - {self.empty_symbol}:
                table.add_prod(t, prod.head, prod)

            if self.empty_symbol in first_body:
                for t in self.follows[prod.head]:
                    table.add_prod(t, prod.head, prod)

        return table
