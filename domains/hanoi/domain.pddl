(define (domain hanoi)
	(:requirements :strips :typing)
	(:types thing - object)
	(:predicates 
		(clear ?x - thing)
        	(on ?x ?y - thing)
        	(smaller ?x ?y - thing)
	)

	(:action move
		:parameters (?disc ?from ?to - thing)
		:precondition (and (smaller ?to ?disc) 
                   			(on ?disc ?from) 
                   			(clear ?disc) 
                   			(clear ?to))
		:effect  (and (clear ?from) 
              		(on ?disc ?to) 
              		(not (on ?disc ?from))  
              		(not (clear ?to)))
	)
)
