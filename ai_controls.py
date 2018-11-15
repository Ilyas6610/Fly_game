from multiprocessing import Process
from messages import *
import pyglet
import math
import messages
from obj_def import *
from random import *
from pyglet.window import key as pygletkey

from keras.models import load_model
model = load_model('model')

class AIcontrolsState:
    Start, Run, Exit = range(3)


class AIcontrols(Process):
    def __init__(self, messenger):
        super(AIcontrols, self).__init__()
        self.size = 1000
        self.ai_state = AIcontrolsState.Start
        self.messenger = messenger
        self.objects_copy = None
        self.functions = {messages.AIcontrols.Quit: self.stop_ai,
                          messages.AIcontrols.UpdateObjects: self.update_objects,
                          messages.AIcontrols.Run: self.start_ai_controls}

        pyglet.clock.schedule_interval(self.read_mes, 1.0 / 30.0)
        pyglet.clock.schedule_interval(self.recalc, 1.0 / 30.0)

    def read_mes(self, dt):
        if self.ai_state != AIcontrolsState.Exit:
            while True:
                data = self.messenger.get_message(messages.AIcontrols)
                if not data:
                    break
                self.functions[data['func']](**data['args']) if 'args' in data else self.functions[data['func']]()


    def start_ai_controls(self):
        self.ai_state = AIcontrolsState.Run

    def stop_ai(self):
        print("terminating ai controls")
        self.ai_state = AIcontrolsState.Exit

    def update_objects(self, objects_copy):
        self.objects_copy = objects_copy

    def recalc(self, dt):
        if self.ai_state == AIcontrolsState.Run and self.objects_copy is not None:
            for index in range(0, ObjectType.ObjArrayTotal):
                if self.objects_copy[index][ObjectProp.ObjType] == ObjectType.Bot2:
                    pressed = 1
                    x = self.objects_copy[index][ObjectProp.Xcoord]
                    y = self.objects_copy[index][ObjectProp.Ycoord]
                    dir = self.objects_copy[index][ObjectProp.Dir]
                    radius = math.sqrt(abs((x - self.size/2)*(x - self.size/2))+abs((y - self.size/2)*(y - self.size/2)))
                    res = 0

                    xe = self.objects_copy[0][ObjectProp.Xcoord]
                    ye = self.objects_copy[0][ObjectProp.Ycoord]
                    dire = self.objects_copy[0][ObjectProp.Dir]
                    """tmp = np.array([[x / 1000, y / 1000, dir / 360, xe/1000, ye/1000],[x / 1000, y / 1000, dir / 360, xe/1000, ye/1000]], np.float32)
                    X = tmp[0:1, 0:5]"""
                    if(radius > self.size/2-150):
                        tmp = np.array([[x / self.size, y / self.size, dir / 360],
                                        [x / self.size, y / self.size, dir / 360]], np.float32)
                        X = tmp[0:1, 0:3]
                        predictions = model.predict(X)
                        res = (predictions[0][0])
                        print(tmp[0] ," res=",res)
                    else:
                        dest_x = xe - 40 * math.sin(math.radians(dire))
                        dest_y = ye - 40 * math.cos(math.radians(dire))

                        rel_x = dest_x - x
                        rel_y = dest_y - y
                        betta = 0
                        if rel_x > 0 and rel_y > 0:
                            betta = math.degrees(math.atan((abs(rel_x)) / (abs(rel_y) + 0.01)))
                        elif rel_x > 0 and rel_y < 0:
                            betta = 180 - math.degrees(math.atan((abs(rel_x)) / (abs(rel_y) + 0.01)))
                        elif rel_x < 0 and rel_y < 0:
                            betta = 180 + math.degrees(math.atan((abs(rel_x)) / (abs(rel_y) + 0.01)))
                        elif rel_x < 0 and rel_y > 0:
                            betta = 360 - math.degrees(math.atan((abs(rel_x)) / (abs(rel_y) + 0.01)))
                        print(betta, " ",dir)
                        if(dir < betta and abs(dir - betta) < 180 or dir > 270 and betta < 180 - (360 - dir) or
                                betta > 270 and dir > 180 - (360 - betta) and dir < betta):
                            res = 1
                    self.messenger.bot2_set_pressed_key(pressed, round(res))
