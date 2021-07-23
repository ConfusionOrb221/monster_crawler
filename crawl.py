from urllib.request import urlopen
import lxml
from pyquery import PyQuery
from lxml import etree
import json
import re
import time

stats_list = ["Str", "Dex", "Con", "Int", "Wis", "Cha"]

class Stats:
    def __init__(self, strength, dexterity, constitution, intelligence, wisdom, charisma):
        self.stength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

class Monster:
    def __init__(self, name, level, stats, traits, perception, source, languages, skills, ac, fort, ref, will, option, hp, immune, resistances, weaknesses, speed, hp_option, actions):
        self.name = name
        self.level = level
        self.stats = stats
        self.traits = traits
        self.perception = perception
        self.source = source
        self.languages = languages
        self.skills = skills
        self.ac = ac
        self.fort = fort
        self.ref = ref
        self.will = will
        self.option = option
        self.hp = hp
        self.immune = immune
        self.resistances = resistances
        self.weaknesses = weaknesses
        self.speed = speed
        self.hp_option = hp_option
        self.actions = actions

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

def tags():
    html = urlopen("https://2e.aonprd.com/Traits.aspx").read().decode('utf-8')
    pq = PyQuery(html)
    tag = pq('span.trait')
    return tag.find("a").text().split()

def getStats(main_content):
    stats = []
    for var in stats_list:
        x = main_content('b').filter(lambda i, this: PyQuery(this).text() == var)
        x = x.__str__()[x.__str__().index(' ') + 1:].replace(',', '')
        stats.append(int(x))
    return Stats(stats[0], stats[1], stats[2], stats[3], stats[4], stats[5])

def getLang(main_content):
    languages = main_content('a')
    lang_list = []
    for val in languages:
        if any("Languages" in string for string in val.values()):
            lang_list.append(val.getchildren()[0].text)
    return lang_list

def getTraits(main_content):
    traits = main_content.children().filter('span')
    trait_list = []
    for val in traits:
        try:
            if any("trait" in string for string in val.values()):
                if val.text == None:
                    trait_list.append(val.getchildren()[0].text)
                else:
                    trait_list.append(val.text)
        except:
            print("error")
            continue
    return trait_list

def getSkills(main_content):
    skills = main_content('a')
    skill_list = []
    for val in skills:
        if any("Skills" in string for string in val.values()) and not any("General" in string for string in val.values()):
            if(not val.getparent().tag == "u"):
                number = re.findall(r'\b\d+\b', val.tail)
                try: 
                    skill_list.append((val.getchildren()[0].text, int(number[0])))
                except:
                    print("eh i kinda fucked up but idk why")
                    continue
    return skill_list

def getTextToInt(main_content, text):
    temp = main_content('b').filter(lambda i, this: PyQuery(this).text() == text)
    temp = int(re.findall(r'\b\d+\b', temp.__str__()[temp.__str__().index(' ') + 1:])[0])
    return temp

def getImmunities(main_content):
    immunities = main_content('b').filter(lambda i, this: PyQuery(this).text() == "Immunities")
    immune = []
    if immunities.text():
        items = immunities.next_all()
        immunity_list = []
        for var in items:
            if var.text == None or var.tail == None:
                break
            if "Resistances" in var.text or "Weaknesses" in var.text:
                break
            immunity_list.append(var.text.replace(" ", ""))
            immunity_list.append(var.tail.replace(" ", ""))
        if(len(immunity_list)) == 0:
            immunities.wrap('<div></div>')
            arr = immunities.contents()
            for x in arr:
                if not hasattr(x, 'text'):
                    immunity_list.append(x)
        else:
            immunity_list.pop()
        temp = ""
        for x in immunity_list:
            if "," in x:
                if x.count(',') > 1:
                    immune.append(temp.strip())
                    x = x.replace(',','')
                    immune.append(x.strip())
                    temp = ""
                elif len(x) > 1:
                    value = x.index(',')
                    if value < (len(x) / 2):
                        immune.append(temp.strip())
                        temp = ""
                        x = x.replace(',','')
                        temp += x
                    else:
                        x = x.replace(',','')
                        temp += x
                        immune.append(temp.strip())
                        temp = ""
                else:
                    immune.append(temp.strip())
                    temp = ""
            else:
                temp += x + ' '
        immune.append(temp.strip())
        return immune
    else:
        return []

def getResistances(main_content, text):
    resistances = main_content('b').filter(lambda i, this: PyQuery(this).text() == text)
    pq = PyQuery(resistances)
    query = pq.contents()
    immune = []
    if resistances.text():
        items = resistances.next_all()
        options = ""
        try:
            temp = resistances.show().__str__()
            options = temp.split('/b>')[1].strip() + " "
        except:
            print("")
        for var in items:
            if var.text == None:
                try:
                    options += var.getchildren()[0].text.strip() + " "
                    options += var.getchildren()[0].tail.strip() + " "
                except:
                    print("")
            elif var.text == None or var.tail == None:
                break
            elif "Weaknesses" in var.text or "Speed" in var.text:
                break
            else:
                options += var.text.strip() + " "
                options += var.tail.strip() + " "
        options = re.sub(' [^A-Za-z0-9]+ ', '', options).strip()
        return options

def getActions(main_content):
    attacks = main_content('span').filter(lambda i, this: PyQuery(this).has_class('hanging-indent'))
    attacks.wrap('<div></div>')
    array = attacks.contents()
    actions = [];
    for x in array:
        if hasattr(x, 'text'):
            tmp = PyQuery(x)
            action = tmp('img')
            action_type = action.eq(0).attr('alt')
            text = tmp.text()
            if action_type != None:
                text = action_type + " " + text
            actions.append(text) 
    return actions;
    

def monsters():
    i = 5
    html = None
    while True:
        print(i)
        try:
            html = urlopen(f"https://2e.aonprd.com/Monsters.aspx?ID={i}").read().decode('utf-8')
        except:
            i += 1
            continue
        pq = PyQuery(html)
        main_content = pq('span#ctl00_MainContent_DetailedOutput')
        title = main_content('h1.title').eq(0).text()
        level = main_content('h1.title').eq(1).text().split()[-1]
        traits = getTraits(main_content)
        preception = main_content('b').filter(lambda i, this: PyQuery(this).text() == 'Perception')
        preception = preception.__str__()[preception.__str__().index(' ') + 1:]
        source = main_content('a.external-link').text()
        skills = getSkills(main_content)
        lang = getLang(main_content)
        stats = getStats(main_content)
        ac = getTextToInt(main_content, 'AC')
        fort = getTextToInt(main_content, 'Fort')
        ref = getTextToInt(main_content, 'Ref')
        will = main_content('b').filter(lambda i, this: PyQuery(this).text() == 'Will')
        pos = will.__str__().find(';')
        hp = main_content('b').filter(lambda i, this: PyQuery(this).text() == 'HP')
        hp_pos = hp.__str__().find(',')
        immune = getImmunities(main_content)
        resistances = getResistances(main_content, "Resistances")
        weakness = getResistances(main_content, "Weaknesses")
        speed = main_content('b').filter(lambda i, this: PyQuery(this).text() == 'Speed')
        speed = speed.__str__()[speed.__str__().index(' ') + 1:]
        actions = getActions(main_content)
        spells = main_content('b').filter(lambda i, this: PyQuery(this).text().find('Innate Spells') > 0)

        print(spells.next().next().next().next())
        print(spells)
        options = None
        hp_option = None
        if pos > 0:
            options = will.__str__()[pos + 1:len(will.__str__())]
        if hp_pos > 0:
            hp_option = hp.__str__()[hp_pos + 1:len(hp.__str__())].strip()
        will = int(re.findall(r'\b\d+\b', will.__str__()[will.__str__().index(' ') + 1:])[0])
        hp = int(re.findall(r'\b\d+\b', hp.__str__()[hp.__str__().index(' ') + 1:])[0])
        monster = Monster(title, int(level), stats, traits, preception, source, lang, skills, ac, fort, ref, will, options, hp, immune, resistances, weakness, speed, hp_option, actions)
        print(monster.toJSON())
        time.sleep(.1)
        i += 1
        if i >= 1:
            quit()

monsters()