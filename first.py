from random import *
size = 1000
if __name__ == "__main__":
    with open("data_f.txt", 'w') as f:
        for index in range (0, 10000):
            x = random() * size
            y = random() * size
            dir = random() * 360
            res = 0
            if(x <= size/2 and y <= size/2 and (dir <= 45 or dir >= 225)):
                res = 1
            elif (x < size / 2 and y > size / 2 and (dir <= 135 or dir >= 315)):
                res = 1
            elif (x >= size / 2 and y >= size / 2 and (dir >= 45 and dir <= 225)):
                res = 1
            elif (x > size / 2 and y < size / 2 and (dir > 135 and dir < 315)):
                res = 1

            f.write(str(float(x/size)) + ' ' + str(float(y/size)) +
                    ' ' + str(float(dir/360)) + ' ' + str(int(res)) + '\n')

from keras.models import Sequential
from keras.layers import Dense
import numpy as np

dataset = np.loadtxt("data_f.txt", delimiter=" ")
X = dataset[:, 0:3]
Y = dataset[:, 3]
model = Sequential()
model.add(Dense(5, input_dim=3, activation='relu'))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='Adam', metrics=['accuracy'])
model.fit(X, Y, epochs=15)
predictions = model.predict(X)
print(predictions[0:10])
model.save('model_2')