import translate.pddl as pddl
import utils
from translate import instantiate
from translate import numeric_axiom_rules
from collections import defaultdict
import formula

#Filippo Gandolfi - 4112879
#I develop this code with Enrico Casagrande and Alessandro Grattarola
#with the help of our supervisor tutor Francesco Leofante

class Encoder():

    def __init__(self, task, modifier):
        self.task = task
        self.modifier = modifier

        (self.boolean_fluents,
         self.actions,
         self.numeric_fluents,
         self.axioms,
         self.numeric_axioms) = self.ground()

        (self.axioms_by_name,
         self.depends_on,
         self.axioms_by_layer) = self.sort_axioms()

    def ground(self):
        """
        Ground action schemas:
        This operain.pddl home/filippo/Documents/Tacchella/domains/blocktion leverages optimizations
        implemented in the parser of the
        Temporal Fast-Downward planner
        """

        (relaxed_reachable, boolean_fluents, numeric_fluents, actions,
        durative_actions, axioms, numeric_axioms,
        reachable_action_params) = instantiate.explore(self.task)

        return boolean_fluents, actions, numeric_fluents, axioms, numeric_axioms

    def sort_axioms(self):
        """
        Returns 3 dictionaries:
        - axioms sorted by name
        - dependencies between axioms
        - axioms sorted by layer
        """

        axioms_by_name = {}
        for nax in self.numeric_axioms:
            axioms_by_name[nax.effect] = nax

        depends_on = defaultdict(list)
        for nax in self.numeric_axioms:
            for part in nax.parts:
                depends_on[nax].append(part)

        axioms_by_layer, _,_,_ = numeric_axiom_rules.handle_axioms(self.numeric_axioms)

        return axioms_by_name, depends_on, axioms_by_layer


    def createVariables(self, Mgr): #OK
        ### Create boolean variables for boolean fluents ###
        ##Create ids dictionary

        self.booleanvar_dict = defaultdict(dict)        #define a dictionary for the boolean variables
        self.actionvar_dict = defaultdict(dict)         #define a dictionary for the action variables
        self.boolean_variables = defaultdict(dict)
        for step in range(self.horizon+1):
            for fluent in self.boolean_fluents:
                key = str(fluent) + '@' + str(step)     #key defined by the fluent and its step
                value = Mgr.mkVar(key)
                self.booleanvar_dict[str(fluent)][key] = value.id
                self.boolean_variables[key] = value

        ### Create propositional variables for actions ids ###
        self.action_variables = defaultdict(dict)
        for step in range(self.horizon):
            for a in self.actions:
                key = a.name + '@' + str(step)          #key defined by the fluent and its step
                value = Mgr.mkVar(key)
                self.actionvar_dict[str(a)][key] = value.id
                self.action_variables[key] = value


    def encodeInitialState(self, Mgr): #OK
        """
        Encode formula defining initial state
        """
        initial = []                                    #Create the empty list initial

        for fact in self.task.init:
            if utils.isBoolFluent(fact):
                if not fact.predicate == '=':
                    for key in self.boolean_variables:
                        if str(fact)+'@'+str(0) == self.boolean_variables[key].label:       #confront
                            #self.boolean_variables[key].do_print()
                            initial.append(self.boolean_variables[key])            #append the key to initial list

            else:
                raise Exception('Initial condition \'{}\': type \'{}\' not recognized'.format(fact, type(fact)))

        ## Close-world assumption: if fluent is not asserted
        ## in init formula then it must be set to false.

        for variable in self.boolean_variables.values():
            if not variable in initial:
                if variable.label[-1] == '0':
                    variable = Mgr.mkNot(variable)      #Mgr is a global variable, we use it to have always an incremental ID
                    #variable.do_print()
                    initial.append(variable)            #Append the negated initial conditions
        return initial


    def encodeGoalState(self, Mgr):  #CHECKED OK (solo per goal singolo)
        """
        Encode formula defining goal state
        """
        def encodePropositionalGoals(goal=None):

            propositional_subgoal = []                  #Create the empty list

            # UGLY HACK: we skip atomic propositions that are added
            # to handle numeric axioms by checking names.
            axiom_names = [axiom.name for axiom in self.task.axioms]

            if goal is None:
                goal = self.task.goal


            ## Check if goal is just a single atom
            if isinstance(goal, pddl.conditions.Atom):
                if not goal.predicate in axiom_names:
                    for key in self.boolean_variables:
                        if str(goal)+'@'+str(self.horizon) == self.boolean_variables[key].label:    #if its the same
                            propositional_subgoal.append(self.boolean_variables[key])               #append it

            ## Check if goal is a conjunction
            elif isinstance(goal, pddl.conditions.Conjunction):
                for fact in goal.parts:
                    for key in self.boolean_variables:
                        if str(fact)+'@'+str(self.horizon) == self.boolean_variables[key].label:    #if its the same
                            propositional_subgoal.append(self.boolean_variables[key])               #append it

            else:
                raise Exception('Propositional goal condition \'{}\': type \'{}\' not recognized'.format(goal, type(goal)))

            return propositional_subgoal

        goal_1 = []                                 #Create the new empty list for goal

        propositional_subgoal = encodePropositionalGoals()
        for key in propositional_subgoal:
            if key is propositional_subgoal[0]:
                goal = key
            else:
                goal = Mgr.mkAnd(goal, key)        #AND of all key

        goal_1.append(goal)
        return goal_1


    def encodeActions(self, Mgr): #CHECKED OK
        """
        Encode action constraints:
        each action variable implies its preconditions
        and effects
        """

        actions = []


        for step in range(self.horizon):
            for action in self.actions:

                precond = []                #Create the empty list for precondition
                addcond = []                #Create the empty list for the positive effects
                delcond = []                #Create the empty list for the negative effects

                ## Encode preconditions
                for pre in action.condition:
                    prename = str(pre) + "@" + str(step) #Preconditions refers to this step
                    for key in self.boolean_variables:
                        if prename in self.boolean_variables[key].label:
                            if pre.negated == True:
                                a = Mgr.mkNot(self.boolean_variables[key])      #for the negative preconditions
                                precond.append(a)
                            else:
                                precond.append(self.boolean_variables[key])     #append to the preconditions list
                temp = precond[0]
                for i in range(1, len(precond)):
                    temp = Mgr.mkAnd(temp, precond[i])                          #AND of all the elements of the list

                actions.append(Mgr.mkImply(self.action_variables[action.name + "@" + str(step)], temp))

                ## Encode add effects (conditional supported)
                for add in action.add_effects:
                    addname = str(add[1]) + "@" + str(step+1) #Because Effects are made at the next cycle
                    for key in self.boolean_variables:
                        if addname in self.boolean_variables[key].label:
                            addcond.append(self.boolean_variables[key])         #append to the effects list
                temp = addcond[0]
                for i in range(1, len(addcond)):
                    temp = Mgr.mkAnd(temp, addcond[i])

                actions.append(Mgr.mkImply(self.action_variables[action.name + "@" + str(step)], temp))

                ## Encode delete effects (conditional supported)
                for de in action.del_effects:
                    delname = str(de[1]) + "@" + str(step+1)
                    for key in self.boolean_variables:
                        if delname in self.boolean_variables[key].label:
                            variable = Mgr.mkNot(self.boolean_variables[key])
                            delcond.append(variable)                            #append to the negative list
                temp = delcond[0]
                for i in range(1, len(delcond)):
                    temp = Mgr.mkAnd(temp, delcond[i])                          #AND of each elements

                actions.append(Mgr.mkImply(self.action_variables[action.name + "@" + str(step)], temp))

        return actions


    def encodeFrame(self, Mgr): #CHECKED OK
        """
        Encode explanatory frame axioms
        """

        frame = []
        or_impl_1 = []
        or_impl_2 = []

        for step in range(self.horizon):
            ## Encode frame axioms for boolean fluents
            for fluent in self.boolean_fluents:
                f = self.boolean_variables[str(fluent)+"@"+str(step)]                                      #define f as fluent @ step
                fnext = self.boolean_variables[str(fluent)+"@"+str(step+1)]                                #define f_next as f @ step+1
                not_f = Mgr.mkNot(self.boolean_variables[str(fluent)+"@"+str(step)])                       #negate each f
                not_f.label = str(fluent)+"@"+str(step)                                                    #define the label of -f
                not_fnext = Mgr.mkNot(self.boolean_variables[str(fluent) + "@" + str(step+1)])             #negate each f_next
                not_fnext.label = str(fluent) + "@" + str(step+1)                                          #define the label of -f_next
                for action in self.actions:
                    for de in action.del_effects:
                        if str(de[1]) == str(fluent):
                            if self.action_variables[str(action.name) + "@" +str(step)] not in or_impl_1:
                                or_impl_1.append(self.action_variables[str(action.name) + "@" +str(step)]) #Take the action variable w/ the name corresponding to the real action
                    for addname in action.add_effects:
                        if str(addname[1]) == str(fluent):
                            if self.action_variables[str(action.name) + "@" +str(step)] not in or_impl_2:
                                or_impl_2.append(self.action_variables[str(action.name) + "@" +str(step)]) #Take the action variable w/ the name corresponding to the real action

                i = q = 1
                temp = or_impl_1[0]                                      #Initialize temp variable
                temp2 = or_impl_2[0]
                while( i < len(or_impl_1)):
                    temp = Mgr.mkOr(temp, or_impl_1[i])                 #Make or between temp and the new action -> store in temp
                    i += 1
                while( q < len(or_impl_2)):
                    temp2 = Mgr.mkOr(temp2, or_impl_2[q])
                    q += 1

                fanfio = Mgr.mkImply(Mgr.mkAnd(f, not_fnext), temp)     #Do the imply between the "and" result and the "or" result
                fanfio2 =  Mgr.mkImply(Mgr.mkAnd(not_f, fnext), temp2)
                frame.append(fanfio)                                    #Append the result of the firts condition of the EFA
                frame.append(fanfio2)                                   #Append the result of the second condition of the EFA
                #fanfio.do_print()
                #fanfio2.do_print()
                or_impl_1 = []
                or_impl_2= []
        return frame


    def encodeExecutionSemantics(self, Mgr): #CHECKED OK
        #Modifier needed
        return self.modifier.do_encode(self.action_variables, self.horizon, Mgr)



    def encodeAtLeastOne(self, Mgr): #CHECKED OK

        atleastone = []

        or_terms = []
        for step in range(self.horizon):
            for action in self.actions:
                or_terms.append(self.action_variables[str(action.name) + "@" + str(step)])

            i = 1
            temp = or_terms[0]
            while( i < len(or_terms)):
                temp = Mgr.mkOr(temp, or_terms[i])
                i += 1
            atleastone.append(temp)
            or_terms = []
        return atleastone


    def encode(self,horizon, Mgr):
        """
        Basic routine for bounded encoding:
        encodes initial, transition,goal conditions
        together with frame and exclusiveness/mutexes axioms

        """
        pass #Overridden in the following class (NOT TO DO)

    def dump(self):
        print('Dumping encoding')
        raise Exception('Not implemented yet')

class EncoderSAT(Encoder):

    def encode(self,horizon, Mgr):

        self.horizon = horizon

        ## Create variables
        self.createVariables(Mgr)

        ### Start encoding formula ###

        formula = defaultdict(list)

        ## Encode initial state axioms

        formula['initial'] = self.encodeInitialState(Mgr)

        ## Encode goal state axioms

        formula['goal'] = self.encodeGoalState(Mgr)

        ## Encode universal axioms

        formula['actions'] = self.encodeActions(Mgr)

        ## Encode explanatory frame axioms

        formula['frame'] = self.encodeFrame(Mgr)

        ## Encode execution semantics (lin/par)

        formula['sem'] = self.encodeExecutionSemantics(Mgr)

        ## Encode at least one axioms

        formula['alo'] = self.encodeAtLeastOne(Mgr)

        return formula
