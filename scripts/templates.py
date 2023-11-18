import os
import random

import logging
logger = logging.getLogger('discord')

def initialize_templates():
    # make sure the templates/ directory exists
    # needs to include: intros.txt, descriptors.txt, and subjects.txt
    if not os.path.exists('templates'):
        os.makedirs('templates')
        logger.info("templates directory created")
    else:
        logger.info("templates directory already exists")
    
    required_files = ['intros.txt', 'descriptors.txt', 'subjects.txt']  
    for file in required_files:
        if not os.path.exists('templates/' + file):
            f = open('templates/' + file, 'w')
            f.write("DEFAULT TEXT\n")
            f.close()
            logger.info(file + " created")
        else:
            logger.info(file + " already exists")

def add_to_template(line, target):
    # add a new line to a template file
    # newline: string to add to the template
    # target: name of the template file to add to
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()
    total1 = len(lines)
    with open('templates/' + target + '.txt', 'a') as f:
        f.write(line + '\n')
        logger.info("Added '" + line + "' to " + target)
    total2 = clean_template(target) #return length for message
    if total2 > total1:
        return total2
    else:
        logger.info("Failed to add '" + line + "' to " + target)
        return -1

def remove_from_template(line, target):
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()

    found = False
    with open('templates/' + target + '.txt', 'w') as f:
        for l in lines:
            if l.strip("\n") != line:
                f.write(l)
            else:
                found = True
    if not found:
        logger.info("Could not find '" + line + "' in " + target)
        return -1
    else:
        logger.info("Removed " + line + " from " + target)
    return clean_template(target) #return length for message

def clean_template(target):
    # remove any empty lines from a template file    
    # collect and keep only unique lines
    with open('templates/' + target + '.txt', 'r') as f:
        lines = f.readlines()
    cleaned = set() # 'not in' boolean check wasn't working for me
    for l in lines:
        if l.strip("\n") != "":
            if target != 'intros':
                l = l.lower() #convert to lowercase only when not intros list
            cleaned.add(l)
    cleaned = list(cleaned)
    cleaned.sort()
    with open('templates/' + target + '.txt', 'w') as f:
        for l in cleaned:
            f.write(l)
    logger.info("Cleaned " + target)
    #return length for message
    return len(cleaned)

def auto_import():
    #add template lines from autoimport/descriptors/ folder to descriptors.txt
    #add template lines from autoimport/subjects/ folder to subjects.txt
    #add template lines from autoimport/intros/ folder to intros.txt
    initialize_templates()
    logger.info("Auto-importing templates...")
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

    #clean templates
    clean_template('descriptors')
    clean_template('subjects')
    clean_template('intros')

    logger.info("Auto-import complete")

def build_random_message(setting):
    # build a random message from the templates
    with open('templates/intros.txt', 'r') as f:
        intros = f.readlines()
    with open('templates/descriptors.txt', 'r') as f:
        descriptors = f.readlines()
    with open('templates/subjects.txt', 'r') as f:
        subjects = f.readlines()
    intro = random.choice(intros).strip("\n")
    message = "### " + intro + ":"
    for i in range(setting["num_prompts"]):
        descriptor = random.choice(descriptors).strip("\n")
        # 25% chance to add another descriptor, repeating until it doesn't
        if setting["repetition_odds"] > 0:
            while (random.randint(1,setting["repetition_odds"]) == 1) and (len(descriptor) < setting["max_length"]):
                descriptor = descriptor + ", " + random.choice(descriptors).strip("\n")
        subject = random.choice(subjects).strip("\n")
        message = message + "\n* " + descriptor + " " + subject
    return message
