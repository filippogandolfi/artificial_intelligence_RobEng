import sys
import os
from . import arguments
import translate
import subprocess
import re
import utils
from planner import encoder
from planner import modifier
from planner import search
import formula
val_path = '/bin/validate'

Mgr = formula.FormulaMgr()

def main(BASE_DIR):
    ## Parse planner args
    args = arguments.parse_args()
    sys.setrecursionlimit(1000000)          #to avoid the recursion limit problem
    ## Run PDDL translator (from TFD)
    prb = args.problem
    if args.domain:
        domain = args.domain
        task = translate.pddl.open(prb, domain)
    else:
        task = translate.pddl.open(prb)
        domain = utils.getDomainName(prb)

    initial_horizon = 1
    val = BASE_DIR + val_path

    ## Compose encoder and search
    ## according to user flags

    e = encoder.EncoderSAT(task, modifier.LinearModifier())
    s = search.LinearSearch(e, initial_horizon)
    plan = s.do_search(Mgr)

    ## VALidate and print plan
    try:
        if plan.validate(val, domain, prb):
            print('\nPlan found!')
            for k, v in plan.plan.items():
                print('Step {}: {}'.format(k, v))
        else:
            print('Plan not valid, exiting now...')
            sys.exit()
    except:
        print('Could not validate plan, exiting now...')
        sys.exit()


if __name__ == '__main__':
    main()
