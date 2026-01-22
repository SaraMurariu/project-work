import random
from collections import Counter


def split_cities_by_max_load(problem, city_max_loads):
    """
    Convert each city into one or more "virtual nodes" representing partial pickups
    returns: list of virtual nodes: [(city_id, pickup_amount), ...]; --> several cities with the same id's will appear.
    Meaning that the algorithm decided that city had far too much gold and it needed to be split for efficient cos solution
    """
    virtual_nodes = []
    for node in problem.graph.nodes:
        if node == 0: continue # skip depot
        
        remaining_gold = problem.graph.nodes[node]["gold"]
        limit = city_max_loads.get(node, remaining_gold)
        # city max loads is the computed amount of "max gold" associated to each city
        # once the problem is created, the function computes an adaptive max load that should be taken from each city
        # if the city has too much gold, takin the full amount and draggin it around would cause cost inefficiences, and so the gold is separated
        # and cities are split into several 'virtual cities' that the problem treats as separate ones -->  for more parameter discussion see report
        if limit >= remaining_gold:
            virtual_nodes.append((node, remaining_gold))
        else:
            while remaining_gold > 1e-6:
                # for floating point precision; last chunk takes whatever is left
                pickup = min(limit, remaining_gold)
                virtual_nodes.append((node, pickup))
                remaining_gold -= pickup
    return virtual_nodes

def routes_cost(routes, problem, shortest):
    total = 0.0

    for route in routes:
        current = 0 
        load = 0.0

        for node in route:
            city_id, pickup = node 
            
            # DO NOT READ 'gold' FROM problem.graph
            # WRONG: remaining_gold = problem.graph.nodes[city_id]["gold"]
            # through virtual nodes logic, the only gold we need to lookup is the one associated to the city
            # not to the problem
            
            dist = shortest[current][city_id]
            total += dist + (problem.alpha * dist * load) ** problem.beta

            load += pickup
            current = city_id

        dist = shortest[current][0]
        total += dist + (problem.alpha * dist * load) ** problem.beta

    return total




def build_path_from_routes(routes, problem, shortest):
  # convert virtual node routes into final path [(city, gold), ...]
  # takes the hierarchical solution structure used by the optimizer (a List of Lists of virtual nodes) 
  # and flattens it into a single, linear sequence (a List of Tuples), adding return to depot as well
    path = []
    # routes = [ [(1,50kg), (5,6kg)],  [(2,50kg), (3,....)]
    for route in routes:
        for node in route:
            # UNPACK TUPLE
            city_id, pickup = node 
            
            # add exactly this chunk to the path (CAREFUL)
            path.append((city_id, pickup))
            
        # add return to depot necessary ofr logic
        path.append((0, 0))

    return path






# -------- NEIGHBOURHOOD OPERATORS --------
def move_city_virtual(routes):
    routes = [r[:] for r in routes if r]
    if len(routes) < 2:
        return routes

    # randomly
    r1, r2 = random.sample(range(len(routes)), 2)
    node = random.choice(routes[r1])
    routes[r1].remove(node)
    routes[r2].append(node)

    if not routes[r1]:
        del routes[r1]

    return routes

def swap_cities_virtual(routes):
    routes = [r[:] for r in routes if len(r) > 1]
    if not routes:
        return routes

    r = random.choice(routes)
    i, j = random.sample(range(len(r)), 2)
    r[i], r[j] = r[j], r[i]
    return routes

def split_route_virtual(routes):
    routes = [r[:] for r in routes if len(r) > 2]
    if not routes:
        return routes

    r = random.choice(routes)
    cut = random.randint(1, len(r) - 1)
    routes.remove(r)
    routes.append(r[:cut])
    routes.append(r[cut:])
    return routes 

def swap_between_routes_virtual(routes):
    """Swaps a node from route A with a node from route B"""
    routes = [r[:] for r in routes if r]
    if len(routes) < 2: return routes
    r1_idx, r2_idx = random.sample(range(len(routes)), 2)
    r1, r2 = routes[r1_idx], routes[r2_idx]
    if not r1 or not r2: return routes
    i = random.randint(0, len(r1) - 1)
    j = random.randint(0, len(r2) - 1)
    r1[i], r2[j] = r2[j], r1[i]
    return routes

def merge_routes_virtual(routes):
    """Merges two random routes into one"""
    routes = [r[:] for r in routes if r]
    if len(routes) < 2: return routes
    r1_idx, r2_idx = random.sample(range(len(routes)), 2)
    routes[r1_idx].extend(routes[r2_idx])
    del routes[r2_idx]
    return routes

def repair_routes(routes, virtual_nodes):
    """
    Ensure all virtual nodes are present, respecting duplicates; i call thse nodes '''virtual''' because many '''duplicates''' are present:
    of course they are not really duplicates but rather different chunks of the same city with different amounts of gold (their sum should be 
    equal to the tot amount of gold)
    ils and lns operators may cause to drop or destroy parts of a solution; this solution checks for FEASIBILITY
    ROUTES: current working solution (a list of lists)
    VIRTUAL NODES: "Master List" of every single gold chunk that exists in the problem
    """
    # count how many chunks we should have, ie, how many times the city has been split
    required_counts = Counter(virtual_nodes)

    # COUNTER FROM COLLECTIONS LOGIC WAS ADDED --> because of artificial duplicates logic, we might have the same city appearing multiple times 
    # with identical or different gold amounts

    # count how many of each chunk we CURRENTLY have in the routes --> how many chunks this route asks us to take
    # (for efficiency reasons that the route counted)
    current_nodes = [vn for r in routes for vn in r]
    current_counts = Counter(current_nodes)

    missing = []

    # find missing nodes, either artificial or real, that don't appear in our solution but appear in the problem definition, and so we add them
    for vn, count in required_counts.items():
        current_have = current_counts[vn]
        if current_have < count:
            # we are missing (count - current_have) copies of this specific chunk
            diff = count - current_have
            # if we are supposed to have two chunks of (5, 50.0) but we only have one in our current routes, diff becomes 1
            missing.extend([vn] * diff)

    # append missing chunks as new individual routes
    # (the optimizer will later merge these into better routes)
    for vn in missing:
        routes.append([vn])

    # NOTE FOR INEFFICIENCY: if one part of the code generates 33.33333333 and another generates 33.33333334 due to tiny floating-point math differences,
    # Counter will treat them as different items !! --> might be the cause of some inefficient solutions

    # NOTE: this works also for cities that haven't been split, or that have no 'virtual node' logic, ie, cities COUNT=1; handles them the same

    return routes
