from multiprocessing import Process
from aaaaaaa.messages import *
import pyglet
import aaaaaaa.messages as messages
from aaaaaaa.obj_def import *
from random import *
from pyglet.window import key as pygletkey

from keras.models import load_model
model = load_model('model')

class AIcontrolsState:
    Start, Run, Exit = range(3)


class AIcontrols(Process):
    def __init__(self, messenger):
        super(AIcontrols, self).__init__()
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
                    x = np.array([[x / 1000, y / 1000, dir / 360],[x / 1000, y / 1000, dir / 360]], np.float32)
                    X = x[0:1, 0:3]

                    predictions = model.predict(X)
                    res = (predictions[0][0])
                    #print(res)
                    self.messenger.bot2_set_pressed_key(pressed, round(res))
