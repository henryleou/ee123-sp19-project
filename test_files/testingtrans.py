# This object manages all the coodinate manipulation
import copy

import numpy as np
import pandas as pd


class CoordinatesManager():
    def __init__(self, list_of_coordinates, fileName):
        self.red_coordinates = list_of_coordinates[0]
        self.green_coordinates = list_of_coordinates[1]
        self.yellow_coordinates = list_of_coordinates[2]
        self.total_coordinates = list_of_coordinates[3]

        # form: [[x1,y1] , [x2,y2], .....]
        self.editted_red = [i for i in self.red_coordinates]
        self.editted_green = [i for i in self.green_coordinates]
        self.editted_yellow = [i for i in self.yellow_coordinates]
        self.editted_total = [i for i in self.total_coordinates]

        # fileName
        self.fileName = fileName

    def set_fileName(self, fileName):
        self.fileName = fileName

    def get_editted_red(self):
        return self.editted_red

    def get_editted_green(self):
        return self.editted_green

    def get_editted_yellow(self):
        return self.editted_yellow

    def add_cell(self, coordinate, color):
        # coordinate : [x, y]
        if color == 'red':
            self.editted_red.append(coordinate)
            print(self.editted_red)
            print("cell added in red")

        elif color == 'green':
            self.editted_green.append(coordinate)
            print("cell added in green")
            print(self.editted_green)

        elif color == 'yellow':
            self.editted_yellow.append(coordinate)
            print("cell added in yellow")
            print(self.editted_yellow)

        else:
            raise Exception("Can not add cell")
        self.editted_total.append(coordinate)

        print(self.editted_total)

    def find_closest_in_editted(self, coordinate, editted_list):
        near_list = []
        for cell in editted_list:
            print("cell coordinate: ", cell)
            print("mouse coordinate: ", coordinate)
            difference = [coordinate[0] - cell[0], coordinate[1] - cell[1]]
            print("differnce: ", difference)
            one_norm = np.linalg.norm(difference, ord=1)
            print("distance ", one_norm)
            if one_norm < 15:
                near_list.append([one_norm, cell])
        if len(near_list) != 0:
            return near_list
        return False

    def delete_cells(self, coordinate, color_mode):
        remove_coordinate = False
        if color_mode == "red":
            remove_coordinate = self.find_closest_in_editted(coordinate, self.editted_red)
            # print("remove {} in red list".format(remove_coordinate))
            # print("before remove ", self.editted_red)
            # print("after remove ", self.editted_red)

        elif color_mode == "green":
            remove_coordinate = self.find_closest_in_editted(coordinate, self.editted_green)
            # print("remove {} in red list".format(in_green))
            # print("before remove ", self.editted_green)
            # print("after remove ", self.editted_green)

        elif color_mode == "yellow":
            remove_coordinate = self.find_closest_in_editted(coordinate, self.editted_yellow)
            # print("remove {} in red list".format(in_yellow))
            # print("before remove ", self.editted_yellow)
            # print("after remove ", self.editted_yellow)

