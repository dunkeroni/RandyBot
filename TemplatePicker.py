import random
import shutil

import logging
logger = logging.getLogger('discord')

class templatePicker():
    def __init__(self):
        self.templates = {}
        self.templates["descriptors"] = set()
        self.templates["subjects"] = set()
        self.templates["intros"] = set()
        self.listsupdated = False
        self.load_templates()

    def load_templates(self):
        #load templates from templates/ folder
        #descriptors.txt
        #subjects.txt
        #intros.txt
        logger.info("Loading templates...")
        with open('templates/descriptors.txt', 'r') as f:
            for line in f:
                self.templates["descriptors"].add(line.strip("\n"))
        with open('templates/subjects.txt', 'r') as f:
            for line in f:
                self.templates["subjects"].add(line.strip("\n"))
        with open('templates/intros.txt', 'r') as f:
            for line in f:
                self.templates["intros"].add(line.strip("\n"))
        logger.info("Templates loaded")

    def save_templates(self):
        #save templates to templates/ folder
        #descriptors.txt
        #subjects.txt
        #intros.txt

        #if lists weren't updated, don't save
        if not self.listsupdated:
            logger.info("No changes to save")
            return
        self.listsupdated = False
        
        #first convert to lists and sort, convert to lowercase for descriptors and subjects
        descriptors = list(self.templates["descriptors"])
        descriptors = [x.lower() for x in descriptors]
        descriptors.sort()

        subjects = list(self.templates["subjects"])
        subjects = [x.lower() for x in subjects]
        subjects.sort()

        intros = list(self.templates["intros"])
        intros.sort()

        #copy existing files to temporary files
        shutil.copyfile('templates/descriptors.txt', 'templates/descriptors.txt.bak')
        shutil.copyfile('templates/subjects.txt', 'templates/subjects.txt.bak')
        shutil.copyfile('templates/intros.txt', 'templates/intros.txt.bak')

        #write to files
        with open('templates/descriptors.txt', 'w') as f:
            for line in descriptors:
                f.write(line + "\n")
        with open('templates/subjects.txt', 'w') as f:
            for line in subjects:
                f.write(line + "\n")
        with open('templates/intros.txt', 'w') as f:
            for line in intros:
                f.write(line + "\n")
        
        savefailed = False
        #sanity check that files have the right number of lines
        with open('templates/descriptors.txt', 'r') as f:
            descriptors = f.readlines()
        with open('templates/subjects.txt', 'r') as f:
            subjects = f.readlines()
        with open('templates/intros.txt', 'r') as f:
            intros = f.readlines()
        if len(descriptors) != len(self.templates["descriptors"]):
            logger.info("Warning: descriptors.txt has " + str(len(descriptors)) + " lines, but templates has " + str(len(self.templates["descriptors"])) + " lines")
            savefailed = True
        if len(subjects) != len(self.templates["subjects"]):
            logger.info("Warning: subjects.txt has " + str(len(subjects)) + " lines, but templates has " + str(len(self.templates["subjects"])) + " lines")
            savefailed = True
        if len(intros) != len(self.templates["intros"]):
            logger.info("Warning: intros.txt has " + str(len(intros)) + " lines, but templates has " + str(len(self.templates["intros"])) + " lines")
            savefailed = True

        #if sanity check failed, restore from backup
        if savefailed:
            logger.info("Restoring from backup...")
            shutil.copyfile('templates/descriptors.txt.bak', 'templates/descriptors.txt')
            shutil.copyfile('templates/subjects.txt.bak', 'templates/subjects.txt')
            shutil.copyfile('templates/intros.txt.bak', 'templates/intros.txt')
            logger.info("Restore complete")
        else:
            logger.info("Templates saved")
        
    def add_to_template(self, line, target):
        #add a line to a template
        #target is descriptors, subjects, or intros
        #convert to lowercase for descriptors and subjects
        self.listsupdated = True
        if target == 'descriptors' or target == 'subjects':
            line = line.lower()
        self.templates[target].add(line)
        logger.info("Added " + line + " to " + target)
        return len(self.templates[target])
    
    def remove_from_template(self, line, target):
        #remove a line from a template
        #target is descriptors, subjects, or intros
        #convert to lowercase for descriptors and subjects
        self.listsupdated = True
        if target == 'descriptors' or target == 'subjects':
            line = line.lower()
        if line in self.templates[target]:
            self.templates[target].remove(line)
            logger.info("Removed " + line + " from " + target)
            return len(self.templates[target])
        else:
            logger.info("Could not find " + line + " in " + target)
            return -1

    def build_random_message(self, setting: dict):
        # build a random message from the templates
        intros = list(self.templates["intros"])
        intro = random.choice(intros)
        message = "### " + intro + ":"
        for i in range(setting["num_prompts"]):
            prompt_type = random.randint(1,3)
            if prompt_type == 1:
                message = message + "\n* " + self.build_recursive_subject_first(setting)
            elif prompt_type == 2:
                message = message + "\n* " + self.build_recursive_prompt(setting)
            elif prompt_type == 3:
                message = message + "\n* " + self.build_multi_subject(setting)
        return message

    def build_recursive_prompt(self, setting: dict):
        # build a random message from the templates
        descriptors = list(self.templates["descriptors"])
        subjects = list(self.templates["subjects"])
        descriptor = random.choice(descriptors)
        # % chance to add another descriptor, repeating until it doesn't
        if setting["repetition_odds"] > 0:
            while (random.randint(1,setting["repetition_odds"]) == 1) and (len(descriptor) < setting["max_length"]):
                descriptor = descriptor + ", " + random.choice(descriptors)
        subject = random.choice(subjects)
        prompt = descriptor + " " + subject
        return prompt
    
    def build_recursive_subject_first(self, setting: dict):
        # build a random message from the templates
        # ex: Turkey: reptilian, brazilian, octillionaire
        descriptors = list(self.templates["descriptors"])
        subjects = list(self.templates["subjects"])
        descriptor = random.choice(descriptors)
        for i in range(random.randint(0,2)):
            descriptor = descriptor + ", " + random.choice(descriptors)
        subject = random.choice(subjects)
        prompt = subject + ": " + descriptor
        return prompt

    def build_multi_subject(self, setting: dict):
        # decide how many subjects to use
        # ex: Reptilian Turkey, Brazilian Octopus
        num_subjects = random.randint(1,4) // 4 + 1 # 25% chance of 2 subjects, 75% chance of 1 subject
        subjects = list(self.templates["subjects"])
        descriptors = list(self.templates["descriptors"])
        # pick subjects
        prompt = ""
        for i in range(num_subjects):
            if i > 0:
                prompt = prompt + ", "
            prompt = prompt + random.choice(descriptors) + " " + random.choice(subjects)
        return prompt

    def info(self):
        #return lengths of templates
        length = {
            "descriptors": len(self.templates["descriptors"]),
            "subjects": len(self.templates["subjects"]),
            "intros": len(self.templates["intros"])
            }
        return length