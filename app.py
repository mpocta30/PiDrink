from flask import Flask, json, render_template, request
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
    
    bartender.makeDrink(drink, "")

    return ('', 200)


# API to for user to make a drink
@app.route('/changepumps', methods=['POST']) 
def change_pumps(): 

    pumps = request.form['pumps']
    pumps = ast.literal_eval(pumps)
    print(pumps)

    # Change pump configuration
    bartender.changeConfiguration(pumps)

    return ('', 200)
    
  
# main driver function 
if __name__ == '__main__': 

    try: 
        bartender = Bartender()
        bartender.buildMenu()

        # Run bartender using a thread
        thread = threading.Thread(target=bartender.run)
        thread.start()

        app.run(host='0.0.0.0') 

    except KeyboardInterrupt: 
        # Clean exit
        sys.exit(0)

    thread.join()
    sys.exit(0)

