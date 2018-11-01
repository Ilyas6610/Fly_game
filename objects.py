from multiprocessing import Process
import pyglet
import math
import numpy as np
import messages
from pyglet.window import key as pygletkey
from obj_def import *
import sys


class ObjectsState:
    Start, Pause, Run, Exit = range(4)

class Unit:
    MAX_FORWARD_SPEED = 500
    MAX_REVERSE_SPEED = 0
    ACCELERATION = 50
    TURN_SPEED = 20

    def __init__(self, x, y, direction=0.0):
        self.position = (x,y)
        self.direction = direction
        self.speed = 0
        self.k_left = self.k_right = self.k_down = self.k_up = 0

    def _update(self, dt):
        self.speed += (self.k_up - self.k_down) * self.ACCELERATION * dt
        if self.speed > self.MAX_FORWARD_SPEED:
            self.speed = self.MAX_FORWARD_SPEED
        if self.speed < self.MAX_REVERSE_SPEED:
            self.speed = self.MAX_REVERSE_SPEED
        self.direction += (self.k_right - self.k_left) * self.TURN_SPEED * dt
        if(self.direction >= 360):
            self.direction -= 360
        elif(self.direction < 0):
            self.direction += 360

        x, y = (self.position)
        rad = self.direction * math.pi / 180
        x += self.speed * math.sin(rad) * dt
        y += self.speed * math.cos(rad) * dt
        self.x, self.y = (x, y)


class ObjectArray:
    def __init__(self, messenger):
        self.messenger = messenger
        self.objects_width = None
        self.objects_height = None
        self.current_objects = self.generate_empty_objects()

    def set_objects_settings(self, configuration=None):
        if configuration:
            for key in configuration:
                for item in configuration[key]:
                    x, y = item
                    self.add_object(key, x, y)

    def generate_empty_objects(self):
        current_objects = np.zeros((ObjectType.ObjArrayTotal, ObjectProp.Total), dtype=np.int32)
        current_objects[:, 0] = np.arange(ObjectType.ObjArrayTotal)
        return current_objects

    def generate_new_object(self, ind, obj_type, x, y, dir):
        return np.array([ind, obj_type, x, y, dir, 0, 0, 0, 0, 0, 0])

    def add_object(self, unit_type, x, y):
        start, end = ObjectType.offset(unit_type)
        for ind in range(start, end+1):
            #search for empty space for object
            if self.current_objects[ind][ObjectProp.ObjType] == ObjectType.Absent:
                if unit_type == ObjectType.Player1 or unit_type == ObjectType.Bot1:
                    dir = 0
                else: dir = 180

                self.current_objects[ind] = self.generate_new_object(ind, unit_type, x, y, dir)
                return True
        return False

    def get_objects(self, link_only=False):
        if link_only:
            return self.current_objects
        return np.copy(self.current_objects)



class Objects(Process):
    def __init__(self, messenger):
        super(Objects, self).__init__()
        self.objects_state = ObjectsState.Start
        self.messenger = messenger
        self.configuration = None
        self.objects = ObjectArray(self.messenger)
        #self.player_action = PlayerAction(self.objects)
        self.functions = {messages.Objects.Quit: self.quit,
                          messages.Objects.AddObject: self.objects.add_object,
                          messages.Objects.Player1SetPressedKey: self.set_pressed_key1,
                          messages.Objects.Player2SetPressedKey: self.set_pressed_key2,
                          messages.Objects.Pause: self.pause_simulation,
                          messages.Objects.Run: self.run_simulation,
                          messages.Objects.UpdateGameSettings: self.update_game_settings}
        #self.objects_state = ObjectsState.Pause

        pyglet.clock.schedule_interval(self.read_mes, 1 / 30.0)
        pyglet.clock.schedule_interval(self.update_units, 1 / 30.0)

    def quit(self):
        self.objects_state = ObjectsState.Exit

    def pause_simulation(self):
        self.objects_state = ObjectsState.Pause

    def run_simulation(self):
        self.objects_state = ObjectsState.Run

    def update_game_settings(self, configuration):
        self.configuration = configuration
        self.objects.set_objects_settings(configuration)

    def set_pressed_key1(self, pushed, key):
        objects = self.objects.get_objects(link_only=True)
        offset = ObjectType.offsets[ObjectType.Player1][0]
        if key == pygletkey.UP:
            objects[offset][ObjectProp.K_up] = pushed
        elif key == pygletkey.DOWN:
            objects[offset][ObjectProp.K_down] = pushed
        elif key == pygletkey.RIGHT:
            objects[offset][ObjectProp.K_right] = pushed
        elif key == pygletkey.LEFT:
            objects[offset][ObjectProp.K_left] = pushed
        self.objects.current_objects = objects

    def set_pressed_key2(self, pushed, key):
        objects = self.objects.get_objects(link_only=True)
        offset = ObjectType.offsets[ObjectType.Player2][0]
        if key == pygletkey.W:
            objects[offset][ObjectProp.K_up] = pushed
        elif key == pygletkey.S:
            objects[offset][ObjectProp.K_down] = pushed
        elif key == pygletkey.D:
            objects[offset][ObjectProp.K_right] = pushed
        elif key == pygletkey.A:
            objects[offset][ObjectProp.K_left] = pushed
        self.objects.current_objects = objects

    def update_units(self, dt):
        if(self.objects_state == ObjectsState.Run):
            objects = self.objects.get_objects(link_only=True)
            for index in range(0, ObjectType.ObjArrayTotal):
                if objects[index][1] != ObjectType.Absent:
                    objects[index][ObjectProp.Velocity] += (objects[index][ObjectProp.K_up] - objects[index][ObjectProp.K_down]) * 80 * dt
                    objects[index][ObjectProp.Dir] += (objects[index][ObjectProp.K_right] - objects[index][ObjectProp.K_left]) * 50 * dt
                    if (objects[index][ObjectProp.Dir] >= 360):
                        objects[index][ObjectProp.Dir] -= 360
                    elif (objects[index][ObjectProp.Dir] < 0):
                        objects[index][ObjectProp.Dir] += 360

                    rad = objects[index][ObjectProp.Dir] * math.pi / 180
                    objects[index][ObjectProp.Xcoord] += objects[index][ObjectProp.Velocity] * math.sin(rad) * dt
                    objects[index][ObjectProp.Ycoord] += objects[index][ObjectProp.Velocity] * math.cos(rad) * dt
            self.objects.current_objects = objects
            self.messenger.game_update_objects(self.objects.get_objects())



    def read_mes(self, dt):
        if self.objects_state != ObjectsState.Exit:
            while True:
                data = self.messenger.get_message(messages.Objects)
                if data == None:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()
                #self.messenger.game_update_objects(self.objects.get_objects())


                #self.messenger.controls_update_objects(self.objects.get_objects())
                #self.messenger.renderer_update_objects(self.objects.get_objects())


"""class PlayerAction:
    def __init__(self, objects_array):
        self.objects = objects_array.get_objects(link_only=True)"""






