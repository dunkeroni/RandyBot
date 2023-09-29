import os
import random

def initialize_templates():
    # make sure the templates/ directory exists
    # needs to include: intros.txt, descriptors.txt, and subjects.txt
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("templates directory created")
    else:
        print("templates directory already exists")
    
    required_files = ['intros.txt', 'descriptors.txt', 'subjects.txt']  
    for file in required_files:
        if not os.path.exists('templates/' + file):
            f = open('templates/' + file, 'w')
            f.write("DEFAULT TEXT\n")
            f.close()
            print(file + " created")
        else:
            print(file + " already exists")

def add_to_template(newline, target):
    # add a new line to a template file
    # newline: string to add to the template
    # target: name of the template file to add to
    with open('templates/' + target + '.txt', 'a') as f:
        f.write(newline + '\n')
        print("Added '" + newline + "' to " + target)
    clean_template(target)

def remove_from_template(line, target):
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()
    with open('templates/' + target + '.txt', 'w') as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
        print("Removed " + line + " from " + target)

def clean_template(target):
    # remove any empty lines from a template file    
    # collect and keep only unique lines
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()
    cleaned = set() # 'not in' boolean check wasn't working for me
    for l in lines:
        if l.strip("\n") != "":
            cleaned.add(l)
    cleaned = list(cleaned)
    cleaned.sort()
    with open('templates/' + target + '.txt', 'w') as f:
        for l in cleaned:
            f.write(l)

    print("Cleaned " + target)

def to_lower(target):
    # convert all lines in a template file to lowercase
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()
    with open('templates/' + target + '.txt', 'w') as f:
        for l in lines:
            f.write(l.lower())

def auto_import():
    #add template lines from autoimport/descriptors/ folder to descriptors.txt
    #add template lines from autoimport/subjects/ folder to subjects.txt
    #add template lines from autoimport/intros/ folder to intros.txt
    initialize_templates()
    print("Auto-importing templates...")
    for file in os.listdir('autoimport/descriptors'):
        if file.endswith('.txt'):
            with open('autoimport/descriptors/' + file, 'r') as f:
                for line in f:
                    add_to_template(line.strip("\n"), 'descriptors')
            #delete the file after importing
            os.remove('autoimport/descriptors/' + file)
    for file in os.listdir('autoimport/subjects'):
        if file.endswith('.txt'):
            with open('autoimport/subjects/' + file, 'r') as f:
                for line in f:
                    add_to_template(line.strip("\n"), 'subjects')
            #delete the file after importing
            os.remove('autoimport/subjects/' + file)
    for file in os.listdir('autoimport/intros'):
        if file.endswith('.txt'):
            with open('autoimport/intros/' + file, 'r') as f:
                for line in f:
                    add_to_template(line.strip("\n"), 'intros')
            #delete the file after importing
            os.remove('autoimport/intros/' + file)

    #convert to lowercase, intros remain capitalized
    to_lower('descriptors')
    to_lower('subjects')
    #clean templates
    clean_template('descriptors')
    clean_template('subjects')
    clean_template('intros')

    print("Auto-import complete")

def build_random_message():
    # build a random message from the templates
    with open('templates/intros.txt', 'r') as f:
        intros = f.readlines()
    with open('templates/descriptors.txt', 'r') as f:
        descriptors = f.readlines()
    with open('templates/subjects.txt', 'r') as f:
        subjects = f.readlines()
    intro = random.choice(intros).strip("\n")
    descriptor = random.choice(descriptors).strip("\n")
    # 25% chance to add another descriptor, repeating until it doesn't
    while random.randint(1,4) == 1:
        descriptor = descriptor + ", " + random.choice(descriptors).strip("\n")
    subject = random.choice(subjects).strip("\n")
    message = intro + ": `" + descriptor + " " + subject + "`"
    return message
