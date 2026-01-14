import random
from .utils import routes_cost, repair_routes


# --------------------------------------------------
# DESTROY OPERATOR
# --------------------------------------------------

def destroy(routes, fraction=0.25):
    """
    Remove a fraction of cities from the current solution.
    In the case of really inefficient routes a move or swap operator may not be enough
    Returns:
      - partial routes
      - list of removed cities
    """
    all_cities = [c for r in routes for c in r] 
    # flatten all cities into a list
    if not all_cities:
        return routes, []

    k = max(1, int(len(all_cities) * fraction)) 
    # k = number of cities to destroy
    removed = set(random.sample(all_cities, k)) 
    # sample the k cities to destroy (at least 1)

    new_routes = []
    for r in routes:
        nr = [c for c in r if c not in removed]
        if nr:
            new_routes.append(nr) 
            # rebuild the route without those cities

    return new_routes, list(removed)


# --------------------------------------------------
# GREEDY REPAIR OPERATOR
# --------------------------------------------------
def greedy_repair(routes, removed, problem, shortest):
    """
    Reinsert removed cities in the cheapest position
    (best marginal cost insertion).
    """
    nodes = [n for n in problem.graph.nodes if n != 0]

    for city in removed: # first for loop --> takes all removed cities and reinserts them
        
        best_cost = float("inf")
        best_routes = None

        # try inserting city in every possible position: in its own route, or within a pre-existing route
        for i in range(len(routes) + 1): # second FOR loop

            if i == len(routes):
                # we reached end of possible r --> CREATE A NEW ROUTE
                trial_routes_partial = routes + [[city]] # temporarily create a new route with that city

                trial_routes_full = repair_routes(trial_routes_partial, nodes)
                # create a temporary full version with repair routes (the other removed notes are put to their own separate routes)
                # we separate full and partial to avoid city duplicates --> repair routes will insert other 'removed' nodes
                cost = routes_cost(trial_routes_full, problem, shortest)
                
                # Check if best
                if cost < best_cost:
                    best_cost = cost
                    best_routes = trial_routes_partial

            else:
                # INSERT INTO EXISTING ROUTE
                for pos in range(len(routes[i]) + 1): # third FOR loop
                    # check which position in said route is the best one to insert the city in
                    trial = routes[i][:pos] + [city] + routes[i][pos:] # temporarily insert in a position
                    trial_routes_partial = routes[:i] + [trial] + routes[i + 1 :]
                    # create trial instertion into a route

                    trial_routes_full = repair_routes(trial_routes_partial, nodes)
                    # same as previous case
                    cost = routes_cost(trial_routes_full, problem, shortest)

                    if cost < best_cost: 
                        # check if it's best insertion up to now for pos
                        best_cost = cost
                        best_routes = trial_routes_partial

        if best_routes is not None: 
            # the algorithm found a better route
            routes = best_routes
        else:
            routes.append([city]) 
            # if no good position for cost decrease was found, simply add to its own route

    return routes


# --------------------------------------------------
# LNS MAIN LOOP
# --------------------------------------------------

def lns(problem, shortest,
        start_routes,
        iterations=100,
        destroy_fraction=0.25):
    """
    Large Neighborhood Search starting from a given solution.
    """
    nodes = [n for n in problem.graph.nodes if n != 0]

    best_routes = start_routes
     # the best solution found so far without implementing LNS
    best_cost = routes_cost(best_routes, problem, shortest)

    for _ in range(iterations):
        # REMOVE
        # rips out 25% (=fraction parameter) of the cities randomly from the solution
        partial, removed = destroy(best_routes, destroy_fraction) 
        # partial is the new trip without the removed nodes
        # removed is a list of the removed nodes

        # REPAIR
        candidate = greedy_repair(partial, removed, problem, shortest)
        # puts the removed nodes using a greedy policy, ie places the city where it adds the least cost
        candidate = repair_routes(candidate, nodes) 
        # sanity check: if there are still nodes not belonging to any route, add them to their own

        cost = routes_cost(candidate, problem, shortest)

        if cost < best_cost:
            best_routes = candidate
            best_cost = cost
        # if randomly deleting some cities from the total trip and them greedily reinserting them improved solution
        # then keep it


    return best_routes
