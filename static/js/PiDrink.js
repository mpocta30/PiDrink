// Hide html elements before page loads
$('#cover').hide();
$('.loading').hide();

// Add drinks to selection list based on current ingredients
$( document ).ready(function() {
    // Turn of async so functions finish
    $.ajaxSetup({
        async: false
    });

    // Create list of ingredients
    var ingredients = [];
    var pumps = [];
    $.getJSON("static/json/pump_config.json", function(json) {
        var keys = Object.keys(json).sort();

        for(var i = 0; i < keys.length; i++) {
            pumps.push(json[keys[i]].value);
        }
        
        for(var i = 0; i < pumps.length; i++) {
            ingredients.push(pumps[i]);
        }
    });


    // Get all possible ingredients
    var option_names = [];
    var option_values = [];
    var pump_names = [];
    var drink_names = [];
    
    $.getJSON("static/json/drink_options.json", function(json) {
        var option_list = json.drink_options.sort();
        for(var i = 0; i < option_list.length; i++) {
            option_names.push(option_list[i].name);
            option_values.push(option_list[i].value);

            // Set names of pumps
            for(var k = 0; k < pumps.length; k++) {
                if(option_list[i].value === pumps[k]) {
                    pump_names.push(option_list[i].name)
                    break;
                }
            }
        }
    });


    // Add drinks to select if proper ingredients work
    $.getJSON("static/json/drink_list.json", function(json) {
        // Tell if drink is cleared or not
        var exists = false;

        $.each(json.drink_list, function(index, value) {
            drink_ings = Object.keys(value.ingredients);

            // Get names of all current drinks
            drink_names.push(value.name.toString().toLowerCase());
            
            // Check if drinks can be made
            for(var i = 0; i < drink_ings.length; i++) {
                if(ingredients.includes(drink_ings[i])) {
                    exists = true;
                }
                else {
                    exists = false;
                    break;
                }
            }
            if(exists === true) {
                drink = value.name.toString();
                $('#drink').append('<option value="'+drink+'">'+drink+'</option>');
            }
          });
    });


    // Set values for pumps
    for(var i = 0; i < option_names.length; i++) {
        $('#pump1').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
        $('#pump2').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
        $('#pump3').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
        $('#pump4').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
        $('#pump5').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
        $('#pump6').append('<option value="'+option_values[i]+'" class="text-center">'+option_names[i]+'</option>');
    }

    // Show current value of pumps
    for(var i = 0; i < pumps.length; i++) {
        $("#pump"+(i+1)+" > [value=" + pumps[i] + "]").attr("selected", "true");
    }


    // Set all ingredient options for new drink
    for(var i = 0; i < option_names.length; i++) {
        $('#ingredient0').append('<option value="'+option_values[i]+'">'+option_names[i]+'</option>');
    }


    // POST request to make drink
    $('#makedrink').submit(function(e) {
        // Prevent page refresh
        e.preventDefault();

        // User confirmation
        if (!confirm("Are you sure you want this drink?")) {
            return;
        }

        // Disable all buttons
        $(':button').prop('disabled', true);

        // Show loading gif
        $('#cover').show();
        $('.loading').show();

        // Send value of select tag
        $.ajax({
            url: '/makedrink',
            type: 'POST',
            data: {
                drink_choice: $('#drink').val(),
            },
            success: function(data) {
                waitTime = data.time;
                setTimeout(function(){
                    // Hide loading gif
                    $('#cover').hide();
                    $('.loading').hide();
                    $(':button').prop('disabled', false);
                    alert("Enjoy your drink!");
                }, waitTime*1000);
            }
        });
    });


    // PUT request for user to make a new drink
    $('#createdrink').submit(function(e) {
        // Prevent page refresh
        e.preventDefault();

        // User confirmation
        if (!confirm("Are you sure you want to create this drink?")) {
            return;
        }

        // Get the form data
        var array = $(this).serializeArray();
        var json = {};
        
        jQuery.each(array, function() {
            json[this.name] = this.value || '';
        });

        // Check if drink already exists
        if(drink_names.includes(json['name'].toLowerCase())){
            alert("This drink alreay exists.");
            return;
        }

        // Send form values
        $.ajax({
            url: '/createdrink',
            type: 'POST',
            data: {
                drink_values: JSON.stringify(json),
            },
            success: function() {
                alert('You have successfully created ' + json['name'] + '!');
            }
        });
    });

    
    // Add new ingredient div
    var ingredient_count = 0;
    $('#add_ingredient').click(function(e) {
        // Prevent page refresh
        e.preventDefault();

        if(ingredient_count === 5) {
            alert('No more than 6 ingredients are allowed.');
            return;
        }

        // Add to ingredient count
        ingredient_count++;

        $('#ingredient_list').append('<div class="row" id="div'+ingredient_count+'"><div class="col-sm-6"><div class="input-group mb-3">\
            <div class="input-group-prepend"><span class="input-group-text" id="basic-addon1">Ingredient</span>\
            </div><select class="form-control text-center" id="ingredient'+ingredient_count+'" name="ingredient'+ingredient_count+'"\
            required><option value="" selecteddisabled>--Ingredient--</option></select>\
            </div></div><div class="col-sm-6"><div class="input-group mb-3">\<div class="input-group-prepend">\
            <span class="input-group-text" id="basic-addon1">Fluid Ounces</span></div><input type="text"\
            class="form-control" id="amount'+ingredient_count+'" name="amount'+ingredient_count+'" placeholder="Ex: 100" required>\
            </div></div></div></div>');

        // Set all ingredient options for new drink
        for(var i = 0; i < option_names.length; i++) {
            $('#ingredient'+ingredient_count).append('<option value="'+option_values[i]+'">'+option_names[i]+'</option>');
        }
    });


    // Remove ingredient div
    $('#remove_ingredient').click(function(e) {
        // Prevent page refresh
        e.preventDefault();

        if(ingredient_count > 0) {

            $('#div'+ingredient_count).remove();

            // Subtract from the ingredient count
            ingredient_count--;
        }
        else {
            alert('Cannot remove all ingredients.')
        }
    });


    // PUT request to change pump configuration
    $('#changepumps').submit(function(e) {
        // Prevent page refresh
        e.preventDefault();

        // User confirmation
        if (!confirm("Are you sure you want to make this changes?")) {
            return;
        }

        // Create list of new pump values
        var pump_values = [];
        for(var i = 1; i < 7; i++) {
            pump_values.push($('#pump'+i).val())
        }

        // Send value of select tag
        $.ajax({
            url: '/changepumps',
            type: 'POST',
            data: {
                pumps: JSON.stringify(pump_values)
            },  
            success: function() {
                alert('Your changes are saved.');
            } 
        });
    });
});