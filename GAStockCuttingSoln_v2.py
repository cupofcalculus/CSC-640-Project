'''
Missouri State University, Fall 2018
Ken Vollmar
Genetic algorithm for stock cutting
Assumptions:
-- Stock and pieces are rectangles with integer coordinates, and
    edges are oriented strictly "north-south" and "east-west." This
    simplifies determining whether two pieces intersect.
-- Assume that the "cut" has zero width, so that two edges may be
    coincident and still valid. Example:  y1 --- yA:::::yB --------y2
-- The size of the stock, and the size and position of all pieces, are
    specified by the upper-left and lower-right corner coordinates.


tkinter documentation:
http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/index.html
https://www.c-sharpcorner.com/blogs/basics-for-displaying-image-in-tkinter-python
https://tkdocs.com/
'''


import time  # for pause during graphic display
import random
import sys
import json
#import tkFont  # http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/fonts.html
# random.seed(0)  # Initialize internal state of the random number generator.
from datetime import datetime
from operator import itemgetter
random.seed(datetime.now())

NUMBER_OF_PIECES = 6  # HARDCODED
STOCK_WIDTH = 800 # HARDCODED  Width of stock
STOCK_HEIGHT = 600 # HARDCODED  Height of stock =
NUMBER_OF_GENERATIONS = 200 # HARDCODED Number of generations of evolution
POPULATION_SIZE = 10  # HARDCODED Number of individuals in population

piece_colors = ["gold", "deepskyblue", "green3", "tan1", "orchid1",
    "purple1", "red2", "palegreen", "goldenrod", "thistle2", "lightblue3",
    "thistle"]

'''
Definition of a class Piece that has data members:
    xcoord	X coordinate of the upper left corner
    ycoord	Y coordinate of the upper left corner
    . . . (other values as desired)

Create an object of the class Piece using     Piece(x, y, ...)
Place an object of the class Piece into a list   myList.append(myPiece)
'''
class Piece:
    def __init__(self, xcoord, ycoord): # Add other values to this list
        self.x = xcoord
        self.y = ycoord
    def setX(self, xcoord):
        self.x = xcoord
    def setY(self, ycoord):
        self.y = ycoord
    def getX(self):
        return self.x
    def getY(self):
        return self.y

    # As you wish, define other function members of class Piece
    # to return other individual values or a set of several
    # values within a tuple or list.

def fitness1(individual):
	'''
	@param individual: a single solution out of the population
	@return: the perimeter of the rectangle
	'''
    # Initialize
	max_x = individual[0]["x2"]
	min_x = individual[0]["x1"]
	max_y = individual[0]["y2"]
	min_y = individual[0]["y1"]
    # Check others
	for i in range(len(individual)):
		if individual[i]["x1"] < min_x:
			min_x = individual[i]["x1"]
		if individual[i]["x2"] > max_x:
			max_x = individual[i]["x2"]
		if individual[i]["y1"] < min_y:
			min_y = individual[i]["y1"]
		if individual[i]["y2"] > max_y:
			max_y = individual[i]["y2"]
    # Set Fitness1
	return 2*(max_x - min_x) + 2*(max_y - min_y)

# Second fitness function which determines overlap sum of an individual by calculating
# the overlap area of all shapes.
def fitness2(individual):
    total_overlap = 0
    for i in range(len(individual)):
        piece = individual[i]
        for j in range(i+1, len(individual)):
            total_overlap += piece_overlap(piece, individual[j])
    return total_overlap

def piece_overlap(p1, p2):
    return max(0, min(p1["x2"], p2["x2"]) - max(p1["x1"], p2["x1"])) * max(0, min(p1["y2"], p2["y2"]) - max(p1["y1"], p2["y1"]))


def copyPieces(original):
    copy = []
    for i in range(len(original)):
        copy.append(copy_piece(original[i]))
    return copy

'''
Create a Piece object in a dictionary data structure, using the parameters
for the piece position.
TBD -- this places the piece within the stock (as opposed to putting
at least the UL corner but not necessarily the LR corner in stock)
'''
# https://www.w3schools.com/python/python_dictionaries.asp
def makeRectObj(i, w, h, x1, y1, c):
    return { "id": i, "width": w, "height": h, "color": c,
        "x1": x1, "y1": y1,
        "x2": x1+w, "y2": y1+h}  # Return a dictionary object

# CROSSOVER HELPER FUNCTION DEFINITION
def crossover(population):
    offsprings = []
    for i in range(POPULATION_SIZE):
        selection1 = random.randint(0, POPULATION_SIZE - 1)
        selection2 = random.randint(0, POPULATION_SIZE - 1)
        cut = random.randint(0, NUMBER_OF_PIECES - 1)

        new_individual = {  "Pieces": [0 for j in range(NUMBER_OF_PIECES)],
                    		"Fitness1": None,
                    		"Fitness2": None }
        transferedPiecesIds = []

        for i in range(cut):
            new_individual["Pieces"][i] = copy_piece(population[selection1]["Pieces"][i])
            transferedPiecesIds.append(population[selection1]["Pieces"][i]["id"])

        for i in range(NUMBER_OF_PIECES):
            if not population[selection2]["Pieces"][i]["id"] in transferedPiecesIds:
                new_individual["Pieces"][i] = copy_piece(population[selection2]["Pieces"][i])
                # print(new_individual["Pieces"][i])
                # print(population[selection2])
                # print(population[selection2]["Pieces"][i])

        offsprings.append(new_individual)

    return offsprings


def copy_piece(original):
    copy = makeRectObj( original["id"],
                        original["width"],
                        original["height"],
                        original["x1"],
                        original["y1"],
                        original["color"])
    return copy

# SELECTION HELPER FUNCTION DEFINITION
def non_dominated_sort(population):
    front0 = []
    # add necessary attributes
    for p in population:
        p["domination_set"] = []
        p["domination_count"] = 0
        p["rank"] = None
    for p in population:
        for q in population:
            if dominates(p, q):    # If p dominates q
                p["domination_set"].append(q)    # Add q to the set of solutions p dominates
            elif dominates(q, p):    # If q dominates p
                p["domination_count"] += 1    # Increment the domination counter of p
        if p["domination_count"] == 0:    # If count == 0, the solution p belongs to the first front
            p["rank"] = 0
            front0.append(p)

    fronts = [front0]
    index = 0
    while len(fronts[index]) != 0:
        next_front = []
        for p in fronts[index]:
            for q in p["domination_set"]:
                q["domination_count"] -= 1
                if q["domination_count"] == 0:
                    q["rank"] = index + 1
                    # check for uniqueness
                    unique = True
                    for i in next_front:
                        if json.dumps(i) == json.dumps(q):
                            unique = False
                    if unique:
                        next_front.append(q)
        index += 1
        fronts.append(next_front)

    return fronts

# HELPER FUNCTION FOR SELECTION
def dominates(p, q):
    # Better solutions have a lower fitness value
    if p["Fitness1"] >= q["Fitness1"] or p["Fitness2"] >= q["Fitness2"]:
        return False
    else:
        return True

def sort_population(population):
    sorted_list = []
    for i in range(len(population)):
        insert_index = 0
        for j in range(len(sorted_list)):
            if population[i]["Fitness2"] > sorted_list[j]["Fitness2"]:
                insert_index += 1
            elif population[i]["Fitness2"] == sorted_list[j]["Fitness2"] and population[i]["Fitness1"] > sorted_list[j]["Fitness1"]:
                insert_index += 1
        sorted_list.insert(insert_index, population[i])

    return sorted_list

# Use tkinter to display stock and pieces
from tkinter import *
root = Tk()
canvas = Canvas(root, width = STOCK_WIDTH, height = STOCK_HEIGHT, bg='khaki')
canvas.pack()



# Read data from a file if a file is given on the command line.
# Open the file and read it into the list "content"
if (len(sys.argv) > 1): # A command-line argument exists; assume it is an input filename
    filename = sys.argv[1]
    '''
    # This section not genuinely indented, but necessary for comment
    else: # Prompt for input filename
    	filename = input("\n\n\tPlease type an input data file name: ")
    '''
    try:
        with open(filename) as f:
            content = f.readlines()
    except FileNotFoundError:
        sys.exit('Could not find file ' + filename)

    # Data in file is expected to be, on separate lines as shown:
    # 	Width of stock
    #	Height of stock
    #	Number of pieces to be cut from stock
    #	Width Height   of piece 0
    #	Width Height   of piece 1
    #		. . .
    #	Width Height   of piece (N-1)
    #
    # Show the data of the input data file, one word at a time
    for i in range(0, len(content)):
        line = content[i].split()
        for j in range(0, len(line)):
            print(str(line[j]))


''' Initialize and display POPULATION_SIZE number of pieces.
TBD -- Initially, create all pieces of _size_ 200x200,
at _positions_ TBD.
TBD -- this places the piece within the stock (as opposed to putting
at least the UL corner but not necessarily the LR corner in stock)
'''
population = [0 for i in range(POPULATION_SIZE)]
# initialize piece sizes
piece_sizes = []
for i in range(POPULATION_SIZE):
    w = random.randint(50, 400)
    h = random.randint(50, 400)
    piece_sizes.append([w,h])
for indiv_count in range(POPULATION_SIZE):
    # individual = [0 for j in range(NUMBER_OF_PIECES)]
    individual = {  "Pieces": [0 for j in range(NUMBER_OF_PIECES)],
                    "Fitness1": None,
                    "Fitness2": None }
    for piece_count in range(NUMBER_OF_PIECES):
        w = piece_sizes[piece_count][0]
        h = piece_sizes[piece_count][1]
        c = piece_colors[piece_count]  # TBD -- need more colors when more pieces
        x1 = random.randint(0, STOCK_WIDTH - w)   # piece is within stock
        y1 = random.randint(0, STOCK_HEIGHT - h)    # piece is within stock

        # An individual is an array of dictionary objects
        individual["Pieces"][piece_count] = makeRectObj(piece_count, w, h, x1, y1, c)
        #print(individual[piece_count])
        #print("	Piece ", piece_count, " x1 is ", (individual[piece_count]).get("x1"))



        # TBD  -- display the  first individual
        # in general, display the fittest individual of this generation
        if indiv_count == 0:
            canvas.create_rectangle(x1, y1, x1+w, y1+h, fill=c, outline='black')
            canvas.update()
            time.sleep(0.02) # HARDCODED

        print("individual  is ", individual)
        print()

    # The population is an array of individual objects
    population[indiv_count] = individual
    print("population[", indiv_count,"] is ", population[indiv_count])
    print()
    #print("Piece ", piece_count, " x1 is ", (population[piece_count]).get("x1")
    #print("Piece ", piece_count, " x1 is ", (population[piece_count])["x1"]
    #print("Piece ", piece_count, " x1 is ", (population[piece_count])["x1"]
    #print(population[piece_count])["x1"]
    #print()

'''
COPY INDIVIDUAL
Create a deep copy of an individual dictionary
'''
def copy_individual(original):
    copy = {"Pieces": [0 for j in range(NUMBER_OF_PIECES)],
            "Fitness1": None,
            "Fitness2": None }
    for i in range(len(original["Pieces"])):
        copy["Pieces"][i] = makeRectObj(
                                original["Pieces"][i]["id"],
                                original["Pieces"][i]["width"],
                                original["Pieces"][i]["height"],
                                original["Pieces"][i]["x1"],
                                original["Pieces"][i]["y1"],
                                original["Pieces"][i]["color"])
    return copy

'''
FULL COPY INDIVIDUAL
Create a deep copy of an individual dictionary
'''
def full_copy_individual(original):
    copy = {"Pieces": [0 for j in range(NUMBER_OF_PIECES)],
            "Fitness1": None,
            "Fitness2": None }
    for i in range(len(original["Pieces"])):
        copy["Pieces"][i] = makeRectObj(
                                original["Pieces"][i]["id"],
                                original["Pieces"][i]["width"],
                                original["Pieces"][i]["height"],
                                original["Pieces"][i]["x1"],
                                original["Pieces"][i]["y1"],
                                original["Pieces"][i]["color"])
        copy["Fitness1"] = original["Fitness1"]
        copy["Fitness2"] = original["Fitness2"]
    return copy

'''
IN BOUNDS
Checks if movement in bounds
'''
def in_bounds_move(piece, new_x, new_y):
    return (new_x >= 0 and
            new_x + piece["width"] <= STOCK_WIDTH and
            new_y >= 0 and
            new_y + piece["height"] <= STOCK_HEIGHT)


'''
IN BOUNDS ROTATE
Checks if rotation in bounds
'''
def in_bounds_rotate(piece):
    return (piece["x1"] + piece["height"] >= 0 and
            piece["x1"] + piece["height"] <= STOCK_WIDTH and
            piece["y1"] + piece["width"] >= 0 and
            piece["y1"] + piece["width"] <= STOCK_HEIGHT)


'''
MUTATION FUNCTION
This function takes in the current population and current generation number.
N number of individuals are in a population, N number of copies are made
    (an individual in the population can be copies more than once and not
    every individual has to be copied)
Each copy is then randomly mutated at a mutation_rate that scales with the generation number.
A mutation MAY change:
    - Swapping positions of pieces
    - Moving a pieces X and/or Y position
    - Rotating (swapping the height and width of a piece)
'''
def create_mutated_copies(original_population, generation_num):
    mutation_scale = generation_num / 10 if (generation_num / 10 > 1) else 1.0
    mutation_rate = 1.0 * 0.9**(generation_num/mutation_scale)
    mutated_copies = []
    for i in range(len(original_population)):
        # Copy a random individual
        copy_indx = random.randint(0, (len(original_population) - 1))
        copy = copy_individual(original_population[copy_indx])
        mutated = False
        # Swapping Mutation
        max_swaps = round(len(original_population) * mutation_rate)
        num_swaps = random.randint(0, max_swaps)
        for j in range(num_swaps):
            # Grab random indexes to swap positions
            indx1 = random.randint(0, len(copy["Pieces"]) - 1)
            indx2 = random.randint(0, len(copy["Pieces"]) - 1)
            # Get (x,y) positions
            x1 = copy["Pieces"][indx1]["x1"]
            y1 = copy["Pieces"][indx1]["y1"]
            x2 = copy["Pieces"][indx2]["x1"]
            y2 = copy["Pieces"][indx2]["y1"]
            # Adjust piece 1
            if in_bounds_move(copy["Pieces"][indx1], x2, y2):
                copy["Pieces"][indx1]["x1"] = x2
                copy["Pieces"][indx1]["x2"] = x2 + copy["Pieces"][indx1]["width"]
                copy["Pieces"][indx1]["y1"] = y2
                copy["Pieces"][indx1]["y2"] = y2 + copy["Pieces"][indx1]["height"]
            # Adjust piece 2
            if in_bounds_move(copy["Pieces"][indx2], x1, y1):
                copy["Pieces"][indx2]["x1"] = x1
                copy["Pieces"][indx2]["x2"] = x1 + copy["Pieces"][indx2]["width"]
                copy["Pieces"][indx2]["y1"] = y1
                copy["Pieces"][indx2]["y2"] = y1 + copy["Pieces"][indx2]["height"]
        # Moving Mutation
        chance_to_move = 1.0 * mutation_rate
        max_move_dist_x = STOCK_WIDTH * mutation_rate / 2
        max_move_dist_y = STOCK_HEIGHT * mutation_rate / 2
        for indx in range(len(copy["Pieces"])):
            randNum = random.uniform(0.0, 1.0)
            if randNum < chance_to_move:
                # Grab random individual
                x_move = random.uniform(-max_move_dist_x, max_move_dist_x)
                y_move = random.uniform(-max_move_dist_y, max_move_dist_y)
                new_x = copy["Pieces"][indx]["x1"] + x_move
                new_y = copy["Pieces"][indx]["y1"] + y_move
                if in_bounds_move(copy["Pieces"][indx], new_x, new_y):
                    copy["Pieces"][indx]["x1"] += x_move
                    copy["Pieces"][indx]["x2"] += x_move
                    copy["Pieces"][indx]["y1"] += y_move
                    copy["Pieces"][indx]["y2"] += y_move
        # Rotating Mutation
        chance_of_rotation = .5 * mutation_rate
        for indx in range(len(copy["Pieces"])):
            randNum = random.uniform(0.0, 1.0)
            if randNum < chance_of_rotation and in_bounds_rotate(copy["Pieces"][indx]):
                h = copy["Pieces"][indx]["height"]
                w = copy["Pieces"][indx]["width"]
                copy["Pieces"][indx]["height"] = w
                copy["Pieces"][indx]["width"] = h
                copy["Pieces"][indx]["x2"] = copy["Pieces"][indx]["x1"] + copy["Pieces"][indx]["width"]
                copy["Pieces"][indx]["y2"] = copy["Pieces"][indx]["y1"] + copy["Pieces"][indx]["height"]
        # If the copy was mutated add to list
        mutated_copies.append(copy)
    # Return the mutated individuals
    return mutated_copies


'''
This is the main GA loop, performing the evolutionary sequence of
operations: Evaluation, Selection, Crossover, Mutation.
Remember:
    A POPULATION is a set of POPULATION_SIZE individuals.
    An INDIVIDUAL is a set of PIECE_COUNT pieces.
'''
for looper in range(NUMBER_OF_GENERATIONS):

    # CROSSOVER OPERATION FOR INDIVIDUALS
    offsprings = crossover(population)


    # MUTATION OPERATION FOR INDIVIDUALS
    mutated_copies = create_mutated_copies(population, looper)


    # EVALUATE ALL INDIVIDUALS
    # Combine the original population with crossover and mutated individuals
    total_population = []
    for p in population:
        total_population.append(p)
    for o in offsprings:
        total_population.append(o)
    for m in mutated_copies:
        total_population.append(m)
    # Calculate fitness for all individuals that havesn't been calculated
    for i in range(len(total_population)):
        if total_population[i]["Fitness1"] == None:
        	total_population[i]["Fitness1"] = fitness1(total_population[i]["Pieces"])
        	# print(total_population[i]["Fitness1"])
        if total_population[i]["Fitness2"] == None:
            total_population[i]["Fitness2"] = fitness2(total_population[i]["Pieces"])
            # print(total_population[i]["Fitness2"])


    # SELECT INDIVIDUALS FOR REPRODUCTION IN THE NEXT GENERATION
    sorted_population = sort_population(total_population)
    new_population = []
    # for i in range(len(sorted_population)):
    #     for j in range(len(sorted_population[i])):
    #         new_population.append(full_copy_individual(sorted_population[i][j]))
    #         if len(new_population) == POPULATION_SIZE:
    #             break
    #     if len(new_population) == POPULATION_SIZE:
    #         break
    for i in range(POPULATION_SIZE):
        new_population.append(sorted_population[i])

    population = new_population
    for i in population:
        print("Fitness2:", i["Fitness2"])
        print("Fitness1:", i["Fitness1"])
        print()

    # Print highest fitness
    print("Total Population:", str(len(total_population)))
    print("Sorted Population:", str(len(sorted_population)))
    print("New Population:", len(new_population))
    print("Generation " + str(looper))
    print("Fitness 1: " + str(population[0]["Fitness1"]))
    print("Fitness 2: " + str(population[0]["Fitness2"]))
    print()

    # Display all pieces in their new position.
    # In general, display the fittest individual of this generation.
    # In this demo, display only the first individual.
    # Clear the display by re-drawing the background with no elements
    canvas.create_rectangle(0, 0, STOCK_WIDTH, STOCK_HEIGHT, fill='khaki')
    display_individual = population[0] # display this individual, which is a list of dictionary
    for piece_count in range(NUMBER_OF_PIECES):
        canvas.create_rectangle(display_individual["Pieces"][piece_count]["x1"],
            display_individual["Pieces"][piece_count]["y1"],
            display_individual["Pieces"][piece_count]["x2"],
            display_individual["Pieces"][piece_count]["y2"],
            fill = display_individual["Pieces"][piece_count]["color"],
            outline = "black")
        #tkFont.Font(family='Helvetica',size=36, weight='bold') # http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/fonts.html
        canvas.create_text(display_individual["Pieces"][piece_count]["x1"] + 20,
            display_individual["Pieces"][piece_count]["y1"] + 20,
            text=str(display_individual["Pieces"][piece_count]["id"]))

    canvas.update()
    # time.sleep(1) # HARDCODED TIME -- pause briefly between generations



mainloop()   # Graphics loop -- This statement follows all other statements
