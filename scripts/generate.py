import os
import re
import random
import requests
import shutil
import math
from urllib.request import urlretrieve
from ctransformers import AutoModelForCausalLM
from llama_cpp import Llama
from text2pixart import generate_pixelart, generate_sprite, generate_panorama
from text2audio import generate_audio, generate_short_audio
from text2shape import generate_shape

HOST = 'localhost:5000'
URI = f'http://{HOST}/api/v1/generate'

SEED = 0

sumprompt = ''

#llm = AutoModelForCausalLM.from_pretrained("TheBloke/LLaMA2-13B-Tiefighter-GGUF", model_file="llama2-13b-tiefighter.Q4_K_M.gguf", model_type="llama", gpu_layers=35)
llm = 0

def prep(prompt):
    return '''Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
''' + prompt + '''

### Response:'''

def run_llm2(llm, name, prompt):
    if not os.path.exists(name + '/log.txt'):
        f = open(name + '/log.txt', "x")
        f.close()
    f = open(name + '/log.txt', "a")
    f.write('User: \n' + prompt + '\n')
    print('User: \n' + prompt + '\n')
    
    result = llm(prep(prompt))
    f.write('AI: \n' + result + '\n')
    print('AI: \n' + result + '\n')

def run_llm(llm, name, prompt):
    if not os.path.exists(name + '/log.txt'):
        f = open(name + '/log.txt', "x")
        f.close()
    f = open(name + '/log.txt', "a")
    f.write('User: \n' + prompt + '\n')
    print('User: \n' + prompt + '\n')

    request = {
        'prompt': prep(prompt),
        'max_new_tokens': 2000,
        'auto_max_new_tokens': False,
        'max_tokens_second': 0,
        'preset': 'None',
        'do_sample': True,
        'temperature': 0.7,
        'top_p': 0.1,
        'typical_p': 1,
        'epsilon_cutoff': 0,  # In units of 1e-4
        'eta_cutoff': 0,  # In units of 1e-4
        'tfs': 1,
        'top_a': 0,
        'repetition_penalty': 1.18,
        'repetition_penalty_range': 0,
        'top_k': 40,
        'min_length': 100,
        'no_repeat_ngram_size': 0,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1,
        'early_stopping': False,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'grammar_string': '',
        'guidance_scale': 1,
        'negative_prompt': '',
        'seed': SEED,
        'add_bos_token': True,
        'truncation_length': 4096,
        'ban_eos_token': False,
        'custom_token_bans': '',
        'skip_special_tokens': True,
        'stopping_strings': []
    }
    while True:
        response = requests.post(URI, json=request)

        if response.status_code == 200 and len(response.json()['results'][0]['text']) > 0:
            result = response.json()['results'][0]['text']
            f.write('AI: \n' + result + '\n')
            print('AI: \n' + result + '\n')
            #sumprompt += result
            return result
        request['prompt'] += '\n'
    return ''

def model_api(request):
    response = requests.post(f'http://{HOST}/api/v1/model', json=request)
    return response.json()

def model_load():
    return model_api({'action': 'load', 'model_name': 'chimera.gguf'})

def model_unload():
    return model_api({'action': 'unload', 'model_name': 'chimera.gguf'})

def extract_desc_and_names(text):
    pairs = text.split("NAME: ")[1:]
    name_desc_list = []
    for pair in pairs:
        res = pair.split("DESC:")
        if len(res) > 1:
            name, desc = res[0], res[1]
            numbers = re.findall(r'(\d+)', desc.strip())
            name_desc_list.append((name.strip(), desc.strip(), numbers[-1] if len(numbers) > 0 else '0' ))
    return name_desc_list

def extract_desc_and_names2(text):
    pattern = r'\d+\.\s+(.*?):\s+(.*?)\s+(?=\d+)'
    matches = re.findall(pattern, text + ' 0')
    return matches

def save_name_desc(nd, file_path):
    f = open(file_path, "a")
    f.write(nd[0] + '\n')
    f.write(nd[1])
    if len(nd) > 2:
        f.write(str(nd[2]))
    f.close()

def get_font(name, path):
    #r = requests.get(url)
    #with open(name + '/font.ttf', 'wb') as outfile:
    #    outfile.write(r.content)
    shutil.copyfile(path, name + '/font.' + path[-3:])

def extract_hex_colors(text):
    pattern = r'#[A-Fa-f0-9]{6}\b'
    hex_colors = re.findall(pattern, text)
    return hex_colors

def generate_area_objects(name, keywords, instructions, world_name, world_desc, idx, dir_, area_name, area_desc, areas, nareas):
    path = dir_ + '/objects.txt'
    already = []
    if os.path.isfile(path):
        f = open(path, mode='r')
        prev_contents = f.read()
        f.close()
        nent = prev_contents.count('entrance')
        pattern = r'entrance [0-9\.]+ [0-9\.]+ (\d+)'
        matches = re.findall(pattern, prev_contents)
        already = [int(m) for m in matches]
    else:
        nent = 0
    f = open(path, "a")
    if idx == 0:
        x = random.random() * 2.0 - 1.0
        y = random.random() * 2.0 - 1.0
        f.write(f'sign {x} {y} ../../namedesc.txt\n')
        #f.write(f'sign {x} {y} ../../log.txt\n')
    x = random.random() * 2.0 - 1.0
    y = random.random() * 2.0 - 1.0
    f.write(f'sign {x} {y} namedesc.txt\n') 
    itareas = list(range(nareas))
    random.shuffle(itareas)
    for i in itareas:
        if i == idx or i in already:
            continue
        prob = 1 / (nent + 1)
        r = random.random()
        if r < prob:            
            x = random.random() * 2.0 - 1.0
            y = random.random() * 2.0 - 1.0
            f.write(f'entrance {x} {y} {i}\n')
            dir2 = dir_.replace('/' + str(idx), '/' + str(i))
            f2 = open(dir2 + '/objects.txt', "a")
            x = random.random() * 2.0 - 1.0
            y = random.random() * 2.0 - 1.0
            f2.write(f'entrance {x} {y} {idx}\n')
            f2.close()
            nent += 1
    for i, shp in enumerate(areas[idx]['shapes']):
        x = random.random() * 1.8 - 0.9
        y = random.random() * 1.8 - 0.9
        r = random.randint(1, 10)
        a = random.random() * 2.0 * 3.14159
        x2 = x - math.cos(a) * 0.1
        y2 = y - math.sin(a) * 0.1
        f.write(f'shape {x} {y} shape{i}.obj {r} {a}\n')
        f.write(f'sign {x2} {y2} shapenamedesc{i}.txt\n')

def generate_area_assets(dir_, area):
    generate_short_audio('steps, walking on ' + area['steps'], dir_ + '/steps.wav')
    generate_short_audio(area['entrance_snd'], dir_ + '/enter.wav', False)
    generate_sprite(area['entrance'], dir_ + '/entrance.png')
    generate_pixelart(area['floor'], dir_ + '/floor.png')
    generate_panorama(area['panorama'], dir_ + '/panorama.png')
    generate_audio(area['ambient'], dir_ + '/ambient.wav', 30.0)
    for i, shp in enumerate(area['shapes']):
        generate_shape(shp[1], dir_ + '/shape' + str(i) + '.obj')

def prompt_baseline(keywords, instructions, world_name, world_desc):
    return f'''You are creating a world. Here are some keywords that set the theme: [{keywords}]
Your world name is "{world_name}". And its description is: "{world_desc}"'''
#Keep these guidelines in mind: "{instructions}". Please, follow them in your creative process.\n'''

def prompt_create_world(llm, name, keywords, instructions):
    return run_llm(llm, name, f'''Hello! Lets make a world together! 
I ask you to think creatively and come up with a world. Here are some keywords that set the theme: [{keywords}]
And here are some additional instructions: "{instructions}". Please, follow them in your creative process.
Name of your world should be appropriate for the theme, but try not to make it too generic.
While generating description briefly mention the history of the world and its present state. 
Please, do so in the following format: NAME:... DESC:...''')

def prompt_create_world_colors(llm, name, keywords, instructions, world_name, world_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
What two colors would fit this world theme? One for background and the other for main text color.
List two appropriate colors in hex format. 
Example: #ffffff #ababab
Go.''')

def prompt_create_areas(llm, name, keywords, instructions, world_name, world_desc, nareas):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
Please, create and list {nareas} areas and their descriptions in the following format: 
"1. NAME: description 2. NAME: description 3. NAME: description ..." 
Go.''')

def prompt_create_sign_sprite(llm, name, keywords, instructions, world_name, world_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
Here in {world_name} among others exist some type of object that contains written text. 
Think creatively and describe such object, that would be appropriate for {world_name}.
Concisely describe this object only using nouns and adjectives, separate parts with commas. 
Example: Glossy antique chair, bright red, made of wood 
Go.''')

def prompt_create_sign_texture(llm, name, keywords, instructions, world_name, world_desc, sign_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
Here in {world_name} there are these objects: "{sign_desc}". 
Concisely describe the material and texture of this object using nouns and adjectives, separate parts with commas.
Example: old paper, inscribed with ancient runes
Go.''')

def prompt_create_sign_sound(llm, name, keywords, instructions, world_name, world_desc, sign_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
Here in {world_name} there are these objects: "{sign_desc}". 
Concisely describe the sound this object makes when it is interacted with using nouns and adjectives, separate parts with commas.
Example: quiet creeks, scratching, popping
Go.''')

def prompt_create_area_entrance_sprite(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
There exists some object or entrance that could be used to get to {area_name}.
Concisely describe it in one sentence using nouns and adjectives, separate parts with commas.
Example: cracked pink mirroir, glossy looking
Go.''')

def prompt_create_area_entrance_sound(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, entrance_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
There exists this: "{entrance_desc}".
Concisely describe the sound this object makes when it is interacted with using nouns and adjectives.
Example: quiet creeks, scratching, popping
Go.''')

def prompt_create_area_floor_texture(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
Concisely describe the material and the surface of the floor/ground in this area using nouns and adjectives, separate parts with commas.
Example: wet pebbles, dry yellow grass
Go.''')

def prompt_create_area_floor_sound(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, floor_tex):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
The ground in this area can be described as such: "{floor_tex}"
Concisely and realistically describe the sound such surface makes when it is stepped on using nouns and adjectives, separate parts with commas.
Example: steps with loud echo, slimy wet sploches''')

def prompt_create_area_panorama(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
Concisely describe the skybox panorama that would be appropriate for this area, as if instructing another person to draw it digiatally, 
use descriptive words that fit the vibe that you are going for in this area
Go.''')

def prompt_create_area_ambient(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, panorama_desc):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}". The environment here can be described as such: "{panorama_desc}"
Concisely describe how such environment could sound like (or describe an appropriate music track), using nouns and adjectives, separate parts with commas.
Examples: slight ethereal whooshing, occasional owl sounds \n
Go.''')

def prompt_create_area_shape(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, already):
    return run_llm(llm, name, prompt_baseline(keywords, instructions, world_name, world_desc) + f'''
You are creating an area named "{area_name}", its description: "{area_desc}".
You already decribed these objects: {already},
Now describe some other object that also can be found in this area, describe what it is, its shape, how it looks.
Lastly, mention the realistic approximate size of the object. (number from 1 to 10, 1 is like an apple, 10 is like a small building)
IMPORTANT: do so in the following format: NAME:... DESC:... SIZE:...
Example 1: NAME: red car DESC: a big red glossy car with black wheels SIZE: 8
Example 2: NAME: blue flower DESC: a tiny blue flower with yellow center SIZE: 1
Your turn.''')

def generate_colors(llm, name, keywords, instructions, world_name, world_desc):
    answer = prompt_create_world_colors(llm, name, keywords, instructions, world_name, world_desc)
    colors = extract_hex_colors(answer)
    f = open(name + '/colors.txt', "a")
    f.write(colors[0] + '\n')
    f.write(colors[1])
    f.close()

def generate_area_text(llm, name, keywords, instructions, world_name, world_desc, dir_, area_name, area_desc, areas):
    areas.append({})
    print('Generating ' + area_name + '...')
    entrance_prompt = prompt_create_area_entrance_sprite(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc)
    areas[-1]['entrance'] = entrance_prompt
    entrance_snd_prompt = prompt_create_area_entrance_sound(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, entrance_prompt)
    areas[-1]['entrance_snd'] = entrance_snd_prompt
    ground_prompt = prompt_create_area_floor_texture(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc)
    areas[-1]['floor'] = ground_prompt
    steps_prompt = prompt_create_area_floor_sound(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, ground_prompt)
    areas[-1]['steps'] = steps_prompt
    panorama_prompt = prompt_create_area_panorama(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc)
    areas[-1]['panorama'] = panorama_prompt
    ambient_prompt = prompt_create_area_ambient(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, panorama_prompt)
    areas[-1]['ambient'] = ambient_prompt
    already = ""
    areas[-1]['shapes'] = []
    for i in range(3):
        answer = prompt_create_area_shape(llm, name, keywords, instructions, world_name, world_desc, area_name, area_desc, already)
        obj_nd = extract_desc_and_names(answer)
        if len(obj_nd) > 0:
            already += obj_nd[0][0] + ', '
            areas[-1]['shapes'].append(obj_nd[0])
            save_name_desc(obj_nd[0], dir_ + f'/shapenamedesc{i}.txt')

def generate_game(llm, name, keywords, instructions, font_path, seed, nareas):
    SEED = seed
    random.seed(SEED)
    os.makedirs(name)
    world_namedesc = prompt_create_world(llm, name, keywords, instructions)
    world_nd = extract_desc_and_names(world_namedesc)[0]    
    get_font(name, font_path)
    save_name_desc(world_nd, name + '/namedesc.txt')
    world_name, world_desc = world_nd[0], world_nd[1]
    generate_colors(llm, name, keywords, instructions, world_name, world_desc)
    areas_text = prompt_create_areas(llm, name, keywords, instructions, world_name, world_desc, nareas)
    area_nds = extract_desc_and_names2(areas_text)
    os.makedirs(name + '/areas')
    areas = []
    for i in range(len(area_nds)):
        dir_ = name + '/areas/' + str(i)
        os.makedirs(dir_)
        save_name_desc(area_nds[i], dir_ + '/namedesc.txt')
    for i in range(len(area_nds)):
        dir_ = name + '/areas/' + str(i)
        generate_area_text(llm, name, keywords, instructions, world_name, world_desc, dir_, area_nds[i][0], area_nds[i][1], areas)
        generate_area_objects(name, keywords, instructions, world_name, world_desc, i, dir_, area_nds[i][0], area_nds[i][1], areas, nareas)
    sign_prompt = prompt_create_sign_sprite(llm, name, keywords, instructions, world_name, world_desc)
    sign_tex_prompt = prompt_create_sign_texture(llm, name, keywords, instructions, world_name, world_desc, sign_prompt)
    sign_sound_prompt = prompt_create_sign_sound(llm, name, keywords, instructions, world_name, world_desc, sign_prompt)
    model_unload()
    generate_short_audio(sign_sound_prompt, name + '/sign.wav', False)
    generate_sprite(sign_prompt, name + '/sign.png')
    generate_pixelart('flat surface texture ' + sign_tex_prompt, name + '/ui.png')
    for i in range(len(area_nds)):
        dir_ = name + '/areas/' + str(i)
        generate_area_assets(dir_, areas[i])
        
#generate_game('test0', 'lovecraftian cosmic horror', 'gadevox.otf', 69)
#generate_game('test1', 'cool retro godlike pizza', 'impact.otf', 420)
#generate_game('test2', 'planets of the solar system', 'impact.otf', 1011)
#generate_game('test3', 'colorful alien worlds', 'impact.otf', 124213)
#generate_game('test4', 'fast food universe, retro, vhs', 'impact.otf', 1123)
#generate_game('test6', 'retro gaming world, nintendo, 90s', 'pixel.otf', 9)
#generate_game('test7', 'yume nikki', 'pixel.otf', 0)
#generate_game('test8', 'half-life, black mesa, Gordon Freeman', 'pixel.otf', 10)
#generate_game('test9', 'Far Cry is a 2004 first-person shooter game developed by Crytek and published by Ubisoft. It is the first installment in the Far Cry franchise. Set on a mysterious tropical archipelago, the game follows Jack Carver, a former American special operations forces operative, as he searches for the female journalist, Valerie Constantine, who accompanied him to the islands but went missing after their boat was destroyed by mercenaries. As Jack explores the islands, he begins to discover the horrific genetic experiments being conducted on the local wildlife and must confront the mad scientist behind them. ', 'impact.otf', 0)
#generate_game('ss', 'Serious Sam is a video game series created and primarily developed by Croteam. It consists predominantly of first-person shooters. The series follows the advances of mercenary Sam "Serious" Stone against Mental, an extraterrestrial overlord who attempts to destroy humanity at various points in time. The first game, Serious Sam: The First Encounter, was released for Microsoft Windows in March 2001. Several spin-offs were developed by other developers, such as a Palm OS conversion of The First Encounter by InterActive Vision, Serious Sam: Next Encounter (on GameCube and PlayStation 2) by Climax Solent, and Serious Sam Advance (on Game Boy Advance) by Climax London. All three were published by Global Star Software. ', 'impact.otf', 100)

#generate_game("ym4", 'yume nikki, isolation, hikikomori, dream world exploration, depression, anxiety, pixel graphics', 'Try to follow the vibe of the original game as close as possible, its a story of a depressed girl exloring her surreal, traumatized, imaginative mind. Dont forget to mention the retro look of your world, it should be similar to Yume Nikki.', 'pixel.otf', 0, 9)
#generate_game(llm, 'wmcc', 'world of bright neon pixel abomination, surreal and surprising, everything in this world has a twist and a dark mystery, EYES!EYES!EYES!', 'Try to follow the style of this world: backgrounds are dark and objects are bright, neon and simplistic. Generate an interesting and original world!', 'retro.otf', 0, 9)
generate_game(llm, 'mw', 'world of music genres', 'everything here is about music and fancy retro aesthetics', 'impact.otf', 0, 9)
