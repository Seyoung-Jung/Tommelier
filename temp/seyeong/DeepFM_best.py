# -*- coding: utf-8 -*-
"""DeepFM_byDeepctr.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1reESewr_j9KDhTI_ky16ikV61rWgeANf
"""

pip install deepctr


# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/content/drive')

# %cd /content/drive/My Drive/Tobigs/컨퍼런스_와인추천/


import pandas as pd
import numpy as np
from deepctr.models import DeepFM
from deepctr.feature_column import SparseFeat, DenseFeat, get_feature_names
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import tensorflow as tf
from keras.callbacks import EarlyStopping
from sklearn.metrics import accuracy_score, roc_auc_score


train_df = pd.read_json('Data_최종본/train_all_meta_v2.json')
test_df = pd.read_json('Data_최종본/test_all_meta_v2.json')




"""feature : userID, wine_id, food, grapes, region_id, country_code, 연속형 변수"""

X_train = train_df.loc[:,['rating_count','rating_average','body','acidity','alcohol','winery_id','userID','wine_id','food','grapes','region_id','country_code']]
y_train = train_df['like']
X_test = test_df.loc[:,['rating_count','rating_average','body','acidity','alcohol','winery_id','userID','wine_id','food','grapes','region_id','country_code']]
y_test = test_df['like']

# food 리스트 -> str
food_str = []
for i in range(len(X_train['food'])):
    if X_train['food'][i]:food_str.append(' '.join(X_train['food'][i]))
    else:food_str.append(' ')
X_train.food = pd.Series(food_str, name='food')

food_str = []
for i in range(len(X_test['food'])):
    if X_test['food'][i]:food_str.append(' '.join(X_test['food'][i]))
    else:food_str.append(' ')
X_test.food = pd.Series(food_str, name='food')

# grapes 리스트 -> str
grapes_str = []
for i in range(len(X_train['grapes'])):
    if X_train['grapes'][i]:grapes_str.append(' '.join(X_train['grapes'][i]))
    else:grapes_str.append(' ')
X_train.grapes = pd.Series(grapes_str, name='grapes')

grapes_str = []
for i in range(len(X_test['grapes'])):
    if X_test['grapes'][i]:grapes_str.append(' '.join(X_test['grapes'][i]))
    else:grapes_str.append(' ')
X_test.grapes = pd.Series(grapes_str, name='grapes')

# region_id -> int
X_train.region_id.fillna(0, inplace=True)
X_test.region_id.fillna(0, inplace=True)
X_train.region_id = X_train.region_id.astype(int)
X_test.region_id = X_test.region_id.astype(int)

# winery_id -> int
X_train.winery_id.fillna(0, inplace=True)
X_test.winery_id.fillna(0, inplace=True)
X_train.winery_id = X_train.winery_id.astype(int)
X_test.winery_id = X_test.winery_id.astype(int)

# country_code
X_train.country_code.fillna('un', inplace=True)
X_test.country_code.fillna('un', inplace=True)




"""embedding_dim 32로 늘리고 early_stopping train accuracy로 걸어두는 경우 **(dropout & batchnormalization O)**"""

# parameters
BATCH_SIZE = 256
EPOCHS = 500
EMBEDDING_DIM = 32
DROPOUT_RATE = 0.25
early_stopping = EarlyStopping(monitor='accuracy', verbose=1, patience=10)


sparse_features = ['userID', 'wine_id', 'food', 'grapes', 'region_id', 'country_code', 'winery_id']

dense_features = ['rating_count', 'rating_average', 'body', 'acidity', 'alcohol']

for feat in sparse_features:
    lbe = LabelEncoder()
    all = pd.concat([X_train[feat], X_test[feat]], axis=0).drop_duplicates() # train, test 전체를 묶어서 LabelEncoder fit
    lbe = lbe.fit(all)
    X_train[feat] = lbe.transform(X_train[feat])
    X_test[feat] = lbe.transform(X_test[feat])
    if feat == 'wine_id':wine_id_lbe = lbe
    if feat == 'food':food_lbe = lbe
    if feat == 'grapes':grapes_lbe = lbe


mms = MinMaxScaler(feature_range=(0, 1))
X_train[dense_features] = mms.fit_transform(X_train[dense_features])
X_test[dense_features] = mms.transform(X_test[dense_features])

fixlen_feature_columns = [SparseFeat(feat, vocabulary_size=pd.concat([X_train[feat], X_test[feat]], axis=0).drop_duplicates().nunique(),embedding_dim=EMBEDDING_DIM)  # vocabulary_size를 train, test 전체로부터
                           for i,feat in enumerate(sparse_features)] + [DenseFeat(feat, 1,) for feat in dense_features]

dnn_feature_columns = fixlen_feature_columns
linear_feature_columns = fixlen_feature_columns

feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)

# 결측치 mean으로 처리
X_train.fillna(X_train.mean(), inplace=True)
X_test.fillna(X_test.mean(), inplace=True)

train_model_input = {name:X_train[name] for name in feature_names}
test_model_input = {name:X_test[name] for name in feature_names}



model = DeepFM(linear_feature_columns, dnn_feature_columns, task='binary', dnn_dropout=DROPOUT_RATE, dnn_use_bn=True)
model.compile("adam", "binary_crossentropy",metrics=['accuracy'])  # learning rate는 default 0.001

history = model.fit(train_model_input, y_train.values,
                    batch_size=BATCH_SIZE, epochs=EPOCHS, verbose=2, validation_split=0.2, callbacks=[early_stopping])  # 
y_pred = model.predict(test_model_input, batch_size=BATCH_SIZE)
print("test AUC", round(roc_auc_score(y_test.values, y_pred), 4))
print("\ntest Auccuracy", round(accuracy_score(y_test.values, y_pred.round()), 4))

model.summary()






