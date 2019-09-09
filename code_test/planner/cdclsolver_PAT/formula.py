#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 11:23:30 2017

@author: tac
"""


class Variable:

    def __init__(self):
        self.value = 0
        self.pos_lits = list()
        self.neg_lits = list()


class Clause:

    def __init__(self, lit_list):
        self.open = len(lit_list)
        self.subsumer = 0
        self.lit_list = lit_list[:]


class Conflict:
    def __init__(self):
        self.pos = 0
        self.neg = 0


class Formula:
    # open_var       the number of open (unassigned) variables
    # open_cl        the number of open (not subsumed) clauses
    # original_cl    the index below which a clause is not learnt
    # clause_list    the list of Clause objects
    # conflict_list  record number of occurances in conflicts
    # variable_list  the list of Variable objects
    # unit_cl_list   the list of unit clauses
    # emtpy_cl_list  the list of empty clauses

    def __init__(self):
        self.open_var = 0
        self.open_cl = 0
        # Initialize clause list, unit list and empty clauses list
        self.clause_list = list()
        self.variable_list = list()
        self.unit_cl_list = list()
        self.empty_cl_list = list()

        self.open_cl = len(self.clause_list)
        self.original_cl = len(self.clause_list)
        self.conflict_list = [Conflict() for _ in range(len(self.variable_list))]
        return

    def read_cnf(self, fileName):
        inputFile = open(fileName, 'r')
        for line in inputFile:
            if line[0] == 'c':
                pass
            elif line[0] == 'p':
                cleanLine = line.rstrip(' \n')
                elements = cleanLine.split(' ')
                # Initially, all variables are open
                self.open_var = int(elements[-2])
                # NOTICE: variable indexes start from 1, not from 0
                self.variable_list = [Variable() for x in range(self.open_var + 1)]
            else:
                cleanLine = line.rstrip(' \n')
                lit_list = [int(x) for x in cleanLine.split(' ')][:-1]
                # We do not accept empty clauses in the input file
                self.add_clause(lit_list)

        inputFile.close()

        # Initially, all clauses are open
        self.open_cl = len(self.clause_list)
        self.original_cl = len(self.clause_list)
        self.conflict_list = [Conflict() for _ in range(len(self.variable_list))]
        return

    def set_cnf(self, max_index, clauses):
        self.open_var = max_index
        # NOTICE: variable indexes start from 1, not from 0
        self.variable_list = [Variable() for x in range(max_index + 1)]

        for cl in clauses:
            self.add_clause(cl)

        # Initially, all clauses are open
        self.open_cl = len(self.clause_list)
        self.original_cl = len(self.clause_list)
        self.conflict_list = [Conflict() for _ in range(len(self.variable_list))]

    # CDCL has dynamic data structure => add during backtracking
    def add_clause(self, lit_list):
        assert len(lit_list) > 0
        # A new clause is created and added to the list
        clause = Clause(lit_list)
        cl_index = len(self.clause_list)
        self.clause_list.append(clause)
        # Variables must know where they occur positively or negatively
        for l in lit_list:
            v_index = abs(l)
            v = self.variable_list[v_index]
            if l > 0:
                v.pos_lits.append(cl_index)
                if v.value == -1:
                    clause.open -= 1
            else:
                v.neg_lits.append(cl_index)
                if v.value == 1:
                    clause.open -= 1
        # If the clause is unary, then it is added to the list
        if clause.open == 1:
            self.unit_cl_list.append(cl_index)

    def is_satisfied(self):
        return self.open_cl == 0

    def is_contradicted(self):
        return len(self.empty_cl_list) > 0

    def do_eval(self, v_index, value):
        v = self.variable_list[v_index]
        assert v.value == 0
        if value > 0:
            self.do_subsume(v_index, v.pos_lits)
            self.do_simplify(v_index, v.neg_lits)
        elif value < 0:
            self.do_subsume(v_index, v.neg_lits)
            self.do_simplify(v_index, v.pos_lits)
        else:
            # value == 0: Cannot re-assign a value
            return
        v.value = value
        self.open_var = self.open_var - 1
        return

    def undo_eval(self, v_index):
        v = self.variable_list[v_index]
        assert v.value != 0
        if v.value > 0:
            self.undo_subsume(v_index, v.pos_lits)
            self.undo_simplify(v_index, v.neg_lits)
        elif v.value < 0:
            self.undo_subsume(v_index, v.neg_lits)
            self.undo_simplify(v_index, v.pos_lits)
        else:
            # v.value == 0: Cannot undo what has not been done
            return
        v.value = 0
        self.open_var = self.open_var + 1
        return

    def do_subsume(self, v_index, cl_index_list):
        for cl_index in cl_index_list:
            # We do not want to subsume learnt clauses
            if cl_index < self.original_cl:
                cl = self.clause_list[cl_index]
                # Check that we are subsuming the clause for the first time
                if cl.subsumer == 0:
                    cl.subsumer = v_index
                    self.open_cl = self.open_cl - 1
        return

    def undo_subsume(self, v_index, cl_index_list):
        for cl_index in cl_index_list:
            # We do not want to undo subsume on learnt clauses
            if cl_index < self.original_cl:
                cl = self.clause_list[cl_index]
                # Check that we are undoing the assignment to the first subsumer
                if cl.subsumer == v_index:
                    cl.subsumer = 0
                    self.open_cl = self.open_cl + 1
        return

    def do_simplify(self, v_index, cl_index_list):
        for cl_index in cl_index_list:
            cl = self.clause_list[cl_index]
            # update clause even if it is subsumed due to non-chronological backtracking
            cl.open = cl.open - 1
            if cl.subsumer == 0:
                if cl.open == 0:
                    self.empty_cl_list.append(cl_index)
                elif cl.open == 1:
                    self.unit_cl_list.append(cl_index)
        return

    def undo_simplify(self, v_index, cl_index_list):
        for cl_index in cl_index_list:
            cl = self.clause_list[cl_index]
            # update clause even if it is subsumed
            cl.open = cl.open + 1
        return

    def do_print(self):
        v_index = 0
        print("VARIABLES")
        for v in self.variable_list:
            print(v_index, ":", v.value, v.pos_lits, v.neg_lits)
            v_index = v_index + 1
        print("Open:", self.open_var)
        print("\nCLAUSES")
        for cl in self.clause_list:
            print("(", cl.open, ",", cl.subsumer, "):", cl.lit_list)
        print("Open:", self.open_cl)
        print("\nUNIT CLAUSES")
        for cl_index in self.unit_cl_list:
            print(cl_index)
        print("\n\nEMPTY CLAUSES")
        for cl_index in self.empty_cl_list:
            print(cl_index)
        print()