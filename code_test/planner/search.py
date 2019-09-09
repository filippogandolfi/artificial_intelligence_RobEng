from planner import plan as p
from planner import encoder
import utils
import subprocess
import formula as form
#from planner import CDCL_solver
from cdclsolver_PAT import cdcl
from cdclsolver_PAT import heuristics
from cdclsolver_PAT import formula

#Filippo Gandolfi - 4112879
#I develop this code with Enrico Casagrande and Alessandro Grattarola
#with the help of our supervisor tutor Francesco Leofante

class Search():
    def __init__(self, encoder, initial_horizon):
        self.encoder = encoder
        self.horizon = initial_horizon
        self.found = False



class LinearSearch(Search):

    def do_search(self, Mgr):

        CnfFormula= []
        assignment = []

        ## Override initial horizon
        print('Start linear search')

        while not self.found:
            formula_1 = self.encoder.encode(self.horizon, Mgr)
            NnfConverter = form.NnfConversion(Mgr)              #convert to NNF formula
            CnfConverter = form.CnfConversion(Mgr)              #convert to CNF formula
            formula_1and = []
            for key in formula_1:
                for i in range(len(formula_1[key])):
                    formula_1and.append(formula_1[key][i])
            temp = formula_1and[0]
            for j in range(1, len(formula_1and)):
                temp = Mgr.mkAnd(temp, formula_1and[j])

            formulaNnf = NnfConverter.do_conversion(temp)
            CnfConverter.do_conversion(formulaNnf)

            CnfFormula = CnfConverter.get_clauses()
            #creation of the file for minisat from terminal
            inputFile = open("cnfFormula.txt", "w+")
            inputFile.write("p cnf " + str(CnfConverter.manager.lastId) + " " + str(len(CnfFormula)) + "\n")
            q = 0
            while (q < len(CnfFormula)):                        #write the Formula on CNF model
                s = str(CnfFormula[q]).replace('[', '')
                s = s.replace(']', '')
                s = s.replace(',', '')
                inputFile.write(s + " 0\n")
                q += 1
            inputFile.close()
            #fine creazione file

            Formula = formula.Formula()
            Formula.set_cnf(Mgr.lastId + 1, CnfFormula)

            heuristic = heuristics.RandomHeuristic()
            solver = cdcl.Solver(Formula, heuristic, False)     #we use the cdcl solver

            a = solver.run()

            if a:
                self.found = True

                plan = p.Plan(a, self.encoder)
            else:
                self.horizon += 1
                print("\nNew horizon: " + str(self.horizon))

        return plan
        ## Must return a plan object
        ## when plan is found