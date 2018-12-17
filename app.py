from flask import Flask, json, render_template, request, jsonify, abort
from bartender import Bartender
from pprint import pprint

import ast
import threading
import sys
  
app = Flask(__name__) 
  
# Returns home html template
@app.route('/') 
def home(): 
    return render_template('index.html')


# API to for user to make a drink
@app.route('/makedrink', methods=['POST']) 
def make_drink():
    # Make sure a drink isn't already being made
    if bartender.running:
        return "There is already a drink being made\
                        , check back again later.", 503

    # Get drink name
    drink = request.form['drink_choice']

    ingredients, makeTime = bartender.get_ingredients_time(drink)
    
    # Making drink
    thread = threading.Thread(target=bartender.makeDrink, args=(drink, ingredients,))
    thread.start()

    return jsonify(time=makeTime, status=200)


# API for the user to create a new drink
@app.route('/createdrink', methods=['POST']) 
def create_drink(): 
    # Get all values for the drink
    drink_values = request.form['drink_values']
    drink_values = ast.literal_eval(drink_values)

    # Setting the name of the new drink
    drink_name = drink_values['name']

    # Lists to store ingredient information
    ingredients = []
    amounts = []
    ing = {}
    new_drink = {}
    drink_json = {}

    # Decide which values mean what for new drink
    for key in drink_values.keys():
        if 'ingredient' in key:
            ingredients.append(drink_values[key])
        elif 'amount' in key:
            amounts.append(int(drink_values[key]))

    # Create ingredient JSON
    for i, name in enumerate(ingredients):
        ing[name] = amounts[i]

    # Create drink JSON object
    new_drink['name'] = drink_name
    new_drink['ingredients'] = ing

    # Read JSON containing list of drinks
    drink_list = json.load(open('static/json/drink_list.json'))
    drink_list = drink_list['drink_list']

    # Add new drink to drink list
    drink_list.append(new_drink)
    drink_json['drink_list'] = drink_list

    with open("static/json/drink_list.json", "w") as jsonFile:
        json.dump(drink_json, jsonFile)

    return ('', 200)


# API to for user to make a drink
@app.route('/changepumps', methods=['POST']) 
def change_pumps(): 

    pumps = request.form['pumps']
    pumps = ast.literal_eval(pumps)

    # Change pump configuration
    bartender.changeConfiguration(pumps)

    return ('', 200)


# API to add a new ingredient
@app.route('/addingredient', methods=['POST'])
def add_ingredient():
    # Get the information for the new ingredient
    ingredient = request.form['ingredient']

    print(ingredient)
    return ('', 200)
  
# main driver function 
if __name__ == '__main__': 

    try: 
        bartender = Bartender()
        bartender.buildMenu()

        # Run bartender using a thread
        thread1 = threading.Thread(target=bartender.run)
        thread1.start()

        app.run(host='0.0.0.0') 

    except KeyboardInterrupt: 
        # Clean exit
        sys.exit(0)

    thread1.join()
    sys.exit(0)

