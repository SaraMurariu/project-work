import random
import networkx as nx
from .lns import lns

from .utils import (
    build_path_from_routes,
    repair_routes,
    routes_cost,
    move_city,
    swap_cities,
    split_route,
)

def ils(problem, shortest, max_iter=300):
    nodes = [n for n in problem.graph.nodes if n != 0]

    # start with one city per route  --> baseline solution
    routes = [[n] for n in nodes]
    random.shuffle(routes)

    best_routes = routes
    best_cost = routes_cost(best_routes, problem, shortest)

    for _ in range(max_iter):
        # three random mutations: 
        # 1. move: take a city from one route and put it in another
        # 2. swap: swap two cities in the same route
        # 3. split: cut a route into two (creating a new return-to-depot). 
        #   --> if a move reduces the cost (Profit - LoadPenalty), it keeps it
        
        op = random.choice([move_city, swap_cities, split_route])
        candidate = op(best_routes)
        candidate = repair_routes(candidate, nodes)

        cost = routes_cost(candidate, problem, shortest)
        if cost < best_cost:
            best_routes = candidate
            best_cost = cost

    return best_routes

def solve(problem, use_lns=False):
    shortest = dict(
        nx.all_pairs_dijkstra_path_length(problem.graph, weight="dist")
    )

    # always start with ILS
    best_routes = ils(problem, shortest)

    # Optionally refine with LNS (for larger instances)
    if use_lns:
        best_routes = lns(
            problem,
            shortest,
            start_routes=best_routes,
            iterations=80,
            destroy_fraction=0.25,
        )

    return build_path_from_routes(best_routes, problem, shortest)

