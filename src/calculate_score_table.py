from config import *
import pandas as pd
# Start processing:

#changable parameters
points_for_tie_AB = 0.5

points_for_tie_NONE = 0.5

def calculate_score_table(tournament_table, initial_indices, number_of_initial_candidates) :

    score_table = [0.0 for i in range(number_of_initial_candidates)] # initial!
    

    def correct_index(index):
        return initial_indices[index]


    for i in range(len(tournament_table)):
        for j in range(i + 1, len(tournament_table)):
            pair_data = tournament_table[i][j]
            if pair_data is None:
                score_table[correct_index(i)] += points_for_tie_NONE
                score_table[correct_index(j)] += points_for_tie_NONE
            elif (pair_data['winner'] == 'A') :
                score_table[correct_index(i)] += 1
            elif (pair_data['winner'] == 'B') :     
                score_table[correct_index(j)] += 1
            elif (pair_data['winner'] == 'AB') :
                score_table[correct_index(i)] += points_for_tie_AB
                score_table[correct_index(j)] += points_for_tie_AB
    
    return score_table                
                

    
            
