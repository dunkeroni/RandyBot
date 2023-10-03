import random
import shutil

class templatePicker():
    def __init__(self):
        self.templates = {}
        self.templates["descriptors"] = set()
        self.templates["subjects"] = set()
        self.templates["intros"] = set()
        self.load_templates()

    def load_templates(self):
        #load templates from templates/ folder
        #descriptors.txt
        #subjects.txt
        #intros.txt
        print("Loading templates...")
        with open('templates/descriptors.txt', 'r') as f:
            for line in f:
                self.templates["descriptors"].add(line.strip("\n"))
        with open('templates/subjects.txt', 'r') as f:
            for line in f:
                self.templates["subjects"].add(line.strip("\n"))
        with open('templates/intros.txt', 'r') as f:
            for line in f:
                self.templates["intros"].add(line.strip("\n"))
        print("Templates loaded")

    def save_templates(self):
        #save templates to templates/ folder
        #descriptors.txt
        #subjects.txt
        #intros.txt
        
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
            print("Warning: descriptors.txt has " + str(len(descriptors)) + " lines, but templates has " + str(len(self.templates["descriptors"])) + " lines")
            savefailed = True
        if len(subjects) != len(self.templates["subjects"]):
            print("Warning: subjects.txt has " + str(len(subjects)) + " lines, but templates has " + str(len(self.templates["subjects"])) + " lines")
            savefailed = True
        if len(intros) != len(self.templates["intros"]):
            print("Warning: intros.txt has " + str(len(intros)) + " lines, but templates has " + str(len(self.templates["intros"])) + " lines")
            savefailed = True

        #if sanity check failed, restore from backup
        if savefailed:
            print("Restoring from backup...")
            shutil.copyfile('templates/descriptors.txt.bak', 'templates/descriptors.txt')
            shutil.copyfile('templates/subjects.txt.bak', 'templates/subjects.txt')
            shutil.copyfile('templates/intros.txt.bak', 'templates/intros.txt')
            print("Restore complete")
        else:
            print("Templates saved")
        
    def add_to_template(self, line, target):
        #add a line to a template
        #target is descriptors, subjects, or intros
        #convert to lowercase for descriptors and subjects
        if target == 'descriptors' or target == 'subjects':
            line = line.lower()
        self.templates[target].add(line)
        print("Added " + line + " to " + target)
        return len(self.templates[target])
    
    def remove_from_template(self, line, target):
        #remove a line from a template
        #target is descriptors, subjects, or intros
        #convert to lowercase for descriptors and subjects
        if target == 'descriptors' or target == 'subjects':
            line = line.lower()
        if line in self.templates[target]:
            self.templates[target].remove(line)
            print("Removed " + line + " from " + target)
            return len(self.templates[target])
        else:
            print("Could not find " + line + " in " + target)
            return -1

    def build_random_message(self, setting: dict):
        # build a random message from the templates
        intro = random.choice(self.templates["intros"])
        message = "### " + intro + ":"
        for i in range(setting["num_prompts"]):
            descriptor = random.choice(self.templates["intros"])
            # % chance to add another descriptor, repeating until it doesn't
            if setting["repetition_odds"] > 0:
                while (random.randint(1,setting["repetition_odds"]) == 1) and (len(descriptor) < setting["max_length"]):
                    descriptor = descriptor + ", " + random.choice(self.templates["intros"])
            subject = random.choice(self.templates["subjects"])
            message = message + "\n* " + descriptor + " " + subject
        return message

    def info(self):
        #return lengths of templates
        length = {
            "descriptors": len(self.templates["descriptors"]),
            "subjects": len(self.templates["subjects"]),
            "intros": len(self.templates["intros"])
            }
        return length