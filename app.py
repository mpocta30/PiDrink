from flask import Flask, json, render_template, request, jsonify
from bartender import Bartender

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
    drink = request.form['drink_choice']

    ingredients, makeTime = bartender.get_ingredients_time(drink)
    
    thread = threading.Thread(target=bartender.makeDrink, args=(drink, ingredients,))
    thread.start()



    return jsonify(time=makeTime, status=200)


# API to for user to make a drink
@app.route('/changepumps', methods=['POST']) 
def change_pumps(): 

    pumps = request.form['pumps']
    pumps = ast.literal_eval(pumps)

    # Change pump configuration
    bartender.changeConfiguration(pumps)

    return ('', 200)


# API to for user to create a new drink
@app.route('/createdrink', methods=['POST']) 
def create_drink(): 

    pumps = request.form['drink_values']
    print(pumps)

    # Change pump configuration
    #bartender.changeConfiguration(pumps)

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

