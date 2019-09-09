#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  6 10:46:20 2019

@author: tac
"""
import sys

from formula import Formula
from cdcl import Solver
from heuristics import RandomHeuristic, PureMomsHeuristic, VsidsHeuristic

def test_random(inputFile):
    f = Formula(inputFile)
    h = RandomHeuristic()
    s = Solver(f, h, True)
    return s.run()

def test_pure(inputFile):
    f = Formula(inputFile)
    h = PureMomsHeuristic(True)
    s = Solver(f, h, False)
    return s.run()

def test_nopure(inputFile):
    f = Formula(inputFile)
    h = PureMomsHeuristic(False)
    s = Solver(f, h, False)
    return s.run()

def test_vsids(inputFile):
    f = Formula(inputFile)
    h = VsidsHeuristic(255)
    s = Solver(f, h, False)
    return s.run()

if (__name__ == "__main__"):
    print(test_vsids(sys.argv[1]))
#print(test_random(sys.argv[1]))
