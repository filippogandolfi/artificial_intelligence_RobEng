import formula

#Filippo Gandolfi - 4112879
#I develop this code with Enrico Casagrande and Alessandro Grattarola
#with the help of our supervisor tutor Francesco Leofante

class Modifier():
    
    def do_encode(self):
        pass

class LinearModifier(Modifier):


    def do_encode(self, variables, bound, Mgr):
        c = []

        for step in range(bound):                                           #Check steps
           for action in variables:                                         #Take an action
               s = variables[action].label.split('@')
               if int(s[1]) == step:
                   and_terms = []                                           #define the empty list
                   for actions in variables:                                #Take all the other actions
                       if actions != action:
                           s = variables[actions].label.split('@')          #split to extract the step number
                           if int(s[1]) == step:
                               not_actions = Mgr.mkNot(variables[actions])  #Negates all the other actions
                               and_terms.append(not_actions)                #AND of all terms of the list

                   i = 1
                   temp = and_terms[0]
                   while( i < len(and_terms)):
                        temp = Mgr.mkAnd(temp, and_terms[i])
                        i += 1

                   constraint = Mgr.mkImply(variables[action], temp)
                   c.append(constraint)

        return c

        
        
    
    
    
