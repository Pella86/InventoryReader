# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 23:04:29 2019

@author: Mauro
"""

# The program take minecraft screenshots with the inventory open and extract
# the name of the items and the quantity

#==============================================================================
# Imports
#==============================================================================

import PIL

from os import listdir
from os.path import join as fjoin
from os.path import isfile, splitext
from os.path import split as fsplit

import matplotlib.pyplot as plt

#==============================================================================
# Constants and folders
#==============================================================================

# screenshot folder
screenshot_folder = "./screenshots/"

# folder paths
cropped_folder = "./cropped/"
references_folder = "./references/"
num_ref_folder = "./num_ref/"

# file that stores the reference image filenames to item names
ref_namemap_file = fjoin(references_folder , "ref_namemap.txt")

# item frame coordinates in pixels
upper_left_corner = (944, 540)
upper_right_corner = (1016, 540)
lower_left_corner = (943, 607)
lower_right_corner = (1016, 612)

# hotbar coordinates in pixels
upper_left_corner_hotbar = (944, 772)


# item frame measures
tile_width = upper_right_corner[0] - upper_left_corner[0]
tile_height = lower_right_corner[1] - upper_right_corner[1]

# inventory size
inv_cols = 9
inv_rows = 3

# items measures
item_width = 64
item_half_height = 36
border_size = 4

# number position coordinates inside the cropped image
num_upper_left_corner = (24, 40)
num_width = 24
num_height = 28
num_area_width = 20


#==============================================================================
# Image processing
#==============================================================================


# function that takes a screenshot and crops all the relative items in it
def crop_inventory(img):
    # crop inventory
    for i in range(inv_cols):
        for j in range(inv_rows):
            # cut a piece of image
            area = [*upper_left_corner, *lower_right_corner]
            area[0] += i * tile_width
            area[1] += j * tile_height
            area[2] += i * tile_width
            area[3] += j * tile_height
            
            crop = img.crop(area)
           
            crop.save(cropped_folder + f"crop_{i}x{j}.png")   
    
    # crop hotbar
    for i in range(inv_cols):
        area = (upper_left_corner_hotbar[0] + i * tile_width,
                upper_left_corner_hotbar[1],
                upper_left_corner_hotbar[0] + i * tile_width + tile_width,
                upper_left_corner_hotbar[1] + tile_height
                )

        crop = img.crop(area)
        crop.save(cropped_folder + f"crop_hotbar_{i}.png")
        
           
# function that remove borders, and crops the top half of the image
# used for recognition of the object
def get_item(item_image):
    area = (border_size,
            border_size,
            border_size + item_width,
            border_size + item_half_height)
    item = item_image.crop(area)
    return item

# compare two items
def compare(item1, item2):
    for i in range(item1.size[0]):
        for j in range(item1.size[1]):
            if item1.getpixel((i,j)) == item2.getpixel((i, j)):
                continue
            else:
                return False
    return True

# get the image filenames in a folder
def get_images_filename_in_folder(folder):
    files = [fjoin(folder, f)
               for f in listdir(folder)
               if isfile(fjoin(folder, f))
               and splitext(f)[1] == ".png"]    
    return files

# function that keeps only the white pixels
def mask_num(num):
    pixels = num.load()
    for i in range(num.size[0]):
        for j in range(num.size[1]):
            if pixels[i, j] != (255, 255, 255, 255):
                pixels[i, j] = (0, 0, 0, 255) 
    return num

# get the ones in the item number
def get_ones(cropped_image):
    area = ( num_upper_left_corner[0] + num_width, 
             num_upper_left_corner[1],
             num_upper_left_corner[0] + num_width + num_area_width,
             num_upper_left_corner[1] + num_height)  
    
    num = cropped_image.crop(area)
    
    return mask_num(num)

# get the tens in the item number
def get_tens(cropped_image):
    area = (*num_upper_left_corner, 
             num_upper_left_corner[0] + num_area_width,
             num_upper_left_corner[1] + num_height)
    
    num = cropped_image.crop(area)
    return mask_num(num)

# gets the images in a folder loaded as a PIL.Image
def get_images(folder):
    images = []
    filenames = get_images_filename_in_folder(folder)
    
    for filename in filenames:
        im = PIL.Image.open(filename)
        images.append(im)
    return images


#==============================================================================
# Items reference pictures
#==============================================================================

# the reference with filename, name of item, image
class ItemReference:
    
    def __init__(self, filename, name, image):
        self.filename = filename
        self.name = name
        self.image = image 
        
# manages the references
class ItemReferences:
    
    def __init__(self):
        self.references = []
        
        # read the references from the file
        if isfile(ref_namemap_file):
            #parse the file
            with open(ref_namemap_file) as f:
                data = f.read()
                
            for line in data.split("\n"):
                if line:
                    filename, name = line.split("|")
                    im = PIL.Image.open(filename)
                    ir = ItemReference(filename, name, im)
                    self.references.append(ir)
        
        # read the filenames and find out which one has the highest number
        # this will be used to create a new reference filename
        self.incremental_ref_num = 0
        
        for filename in get_images_filename_in_folder(references_folder):
            n = fsplit(filename)[1]
            n = splitext(n)[0]
            n = n.split("_")[1]
            n = int(n)
            if n > self.incremental_ref_num:
                self.incremental_ref_num = n
    
    # compares two items and returns the corresponding string name
    def test_item(self, cropped_image):
        item = get_item(cropped_image)
        item_found = False
        
        # compare items
        for ref in self.references:
            if compare(item, ref.image):
                item_name = ref.name
                item_found = True
        
        if not item_found:
            newref = self.add_new_reference(item)  
            item_name = newref.name
            
        return item_name
              
    # add new reference
    def add_new_reference(self, item):
        plt.imshow(item)
        plt.show()
        
        self.incremental_ref_num += 1
        
        filename = fjoin(references_folder,
                         f"reference_{self.incremental_ref_num}.png")
        
        name = input("Give item name:\n> ")
        
        newir = ItemReference(filename, name, item)
        
        newir.image.save(newir.filename)
        
        self.references.append(newir)
        
        self.save_reference_file()
        
        return newir
        
    # overwrite the file containg image filenames of references
    def save_reference_file(self):

        data = ""
        for ir in self.references:
            data += ir.filename + "|" + ir.name + "\n"
        
        with open(ref_namemap_file, "w") as f:
            f.write(data)
 
#==============================================================================
# Number reference pictures                                
#==============================================================================
        
# class to manage the Reference numbers
class NumRef:
    
    def __init__(self, filename, num, image):
        self.filename = filename
        self.num = num
        self.image = image

# class that manages all the number references
class NumReferences:
    
    def __init__(self):
        # load number references
        num_ref_filenames = get_images_filename_in_folder(num_ref_folder)
        
        self.references = []
        for num_filename in num_ref_filenames:
            n = fsplit(num_filename)[1]
            n = splitext(n)[0]
            n = n[-1]
            
            im = PIL.Image.open(num_filename)
            
            nr = NumRef(num_filename, n, im)
            self.references.append(nr)  

    # reads the number on the cropped item
    def read_quantites(self, cropped_image):
        ones = get_ones(cropped_image)
        tens = get_tens(cropped_image)
        
        onesn, tensn = "0", "0"
        for ref in self.references:
            if compare(ones, ref.image):
                onesn = ref.num
            
            if compare(tens, ref.image):
                tensn = ref.num
                
        return int(tensn + onesn)
    
    # add a number use get_ones() or get_tens()
    def add_reference(self, extracted_num):
        plt.imshow(extracted_num)
        plt.show()
        
        isnum = input("is number: ")
        
        if isnum == "yes" or isnum == "y":
            n = input("which number: ")
            
            filename = "reference_num_" + str(n) + ".png"
            
            extracted_num.save(fjoin(num_ref_folder, filename))        

#==============================================================================
# Minecraft units
#==============================================================================

# small class to represent a number in minecraft 64-based stack
class Stacks:
    
    def __init__(self, n):
        self.n = n
    
    def __str__(self):
        stack_n = int(self.n / 64)
        n = self.n % 64
        s = "" if stack_n == 0 else str(stack_n) + "s"
        
        s = ""
        if stack_n != 0:
            s += str(stack_n) + "s"
        
        if n != 0:
            s += str(n)
            
        if s:
            return s
        else:
            return "0"

#==============================================================================
# Calculate totals from screenshot
#==============================================================================
        
# returns the total quantity per items in a screenshot
def record_totals(path_to_screenshot):

    # initialize the references
    ir = ItemReferences()
    nr = NumReferences()
    
    # open image
    image = PIL.Image.open(path_to_screenshot)
    
    # crop the image and save the objects
    crop_inventory(image)
 
    # get the cropped images
    cropped_images = get_images(cropped_folder)
    
    # store the quantities in a dictionary item:quantity
    sum_item = {}
    
    for image in cropped_images:
        
        item_name = ir.test_item(image)
        
        quantity = nr.read_quantites(image)
        
        if item_name != "Empty" and quantity == 0:
            quantity = 1

        if item_name in sum_item:
            sum_item[item_name] += quantity
        else:
            sum_item[item_name] = quantity
     
    return sum_item

#==============================================================================
# MAIN         
#==============================================================================

if __name__ == "__main__":
    
    pre_mining_screenshot = fjoin(screenshot_folder, "before_mining.png")
    post_mining_screenshot = fjoin(screenshot_folder, "after_mining.png")
    
    time = "12:31"
    first_pickaxe = "Diamond Pickaxe"
    second_pickaxe = "None"
    shovel = "Iron Shovel"
    
    pre_mining = record_totals(pre_mining_screenshot)
    after_mining = record_totals(post_mining_screenshot)
    
    print("Yields after", time, "min mining")
    print("with a", first_pickaxe, "and a", shovel)
    
    for key in after_mining:
        if key in pre_mining:
            yld = after_mining[key] - pre_mining[key] 
        else:
            yld = after_mining[key]
        
        if yld > 0:
            print(f"{key:.<17}", f"{str(Stacks(yld)): <6s}")
    

    
    

       