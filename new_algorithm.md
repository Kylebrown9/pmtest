Goal
Include temporal information in partitioning
Be more explicit about clustering contexts vs. activities
Attempt to partition activities

Algorithm

Take the number of Activities in the system as A
Take the number of Contexts in the system as C

1. Derive a petri net graph from the logs for a given context
(Fast)

DONE

2. Create a matrix from the graph which shows the minimum distance
between any two activities in the graph

TODO:
https://networkx.github.io/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.generic.shortest_path_length.html#networkx.algorithms.shortest_paths.generic.shortest_path_length
Create a dictionary from activity name to matrix index
Convert iterator of (source, dict) pairs into matrice
Fill in all gaps with infinity/none

3. Compare the matrices (AxA) generated from N contexts
  1. Create a matrix (AxA) containing the standard deviation of the distances across the matrices
  2. Create a matrix (AxA) contianing the mean of the distances across the matrices
  Note: The std-dev of values containing inf/none is inf/none,
  the mean of values containing inf/none is inf/none

TODO:
https://docs.scipy.org/doc/numpy/reference/generated/numpy.std.html
https://numpy.org/doc/stable/reference/generated/numpy.mean.html

4. Find sets of activities and contexts which are optimal in the following ways
  * the mean-distance matrix for the contexts contains the activities as connected components
  * Minimize the std-dev-distance matrix for the contexts pairs that include the activities
  * Maximize the number of contexts
  * Maximize the number of activities

  1. Compute the pair-wise combined result (#3) for all pairs of contexts
  2. Score the maximal connected components
  3. 

TODO:


4. Alternative 

Intuition
A common sub-process contains an activity-pair if the directed-shortest-path
between those activities is the same in all of the contexts of the sub-process

Instead of combining activity-pairs together for graphs
Combine graphs together for activity-pairs

1. Generate initial groups
  1. For each graph find the directed-shortest-path between each pair of node
  2. For each pair, emit a record ((src-activity, dest-activity), context, distance)
  3. Do not emit a record for nodes which cannot reach eachother and or not present
  4. Collect these records by the activity-pair
  5. Collect them again by distance
  5. For each collection create a group (set((src-activity, dest-activity, distance)), set(contexts))
       for each distinct distance found, where contexts is the set of contexts from records with this distance

2. Combine groups together

groups = set()
new_groups = ...

# (set((src-activity, dest-activity, distance)), set(contexts)) => number
group_id = {}
# (id, id)
tried_combinations = set()

while new_groups:
   new_groups = set()
   next_groups = set()
   non_maximal = set()

   for g1 in new_groups:
      for g2 in new_groups:
         if g1 == g2:
            continue
         
         maybe_merged = try_merge(g1, g2)

         if maybe_merged:
            next_groups.add(maybe_merged)
            non_maximal.add(g1)
            non_maximal.add(g2)

   for g1 in groups:
      for g2 in new_groups:
         maybe_merged = try_merge(g1, g2)

         if maybe_merged:
            next_groups.add(maybe_merged)
            non_maximal.add(g1)
            non_maximal.add(g2)
    
   groups = groups.union(new_groups).subtract(non_maximal)
   new_groups = next_groups


if edges * contexts increases and the new group would form a connected component, then merge

partition the values found in different graphs into groups
Each group is of the form (set(contexts), set( (src-activity, dest-activity, value_min, value_max) ))
Combine together groups which have overlapping contexts