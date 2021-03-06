# -*- coding: utf-8 -*-
"""
Script to create a segmentation of images with the SegNet network
"""
# ----------------------------------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------------------------------
import os
import numpy as np
import cv2
import progressbar

from tensorflow.python.keras.models import *
from tensorflow.python.keras.layers import *
# from tensorflow.python.keras import backend as back

from cleaning_functions import normalized, one_hot_it, prep_images_folder, plot_validation_info_kfold

# back.set_image_dim_ordering('tf')


# ----------------------------------------------------------------------------------------------------------------------
# Functions definitions
# ----------------------------------------------------------------------------------------------------------------------

def vgg_segnet(nb_classes, img_size, vgg_weights_path, save=False):
    """
    Creates a segmentation model with number of classes and input shape defined by parameters.

    Img_size must be multiple of 32=2e5 so that output and input images get the same size.

    :param nb_classes:
    :type nb_classes:
    :param img_size:
    :type img_size:
    :param vgg_weights_path:
    :type vgg_weights_path:
    :param save:
    :type save:
    :return:
    :rtype:
    """
    # Parameters initialization
    pool_size = 2

    # Layers definition
    encoding_layers = [
        # Block 1
        Conv2D(64, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block1_conv1'),
        Conv2D(64, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block1_conv2'),
        MaxPooling2D(pool_size=(pool_size, pool_size), data_format='channels_last', name='block1_pool'),
        # Block 2
        Conv2D(128, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block2_conv1'),
        Conv2D(128, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block2_conv2'),
        MaxPooling2D(pool_size=(pool_size, pool_size), data_format='channels_last', name='block2_pool'),
        # Block 3
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv1'),
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv2'),
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv3'),
        MaxPooling2D(pool_size=(pool_size, pool_size), data_format='channels_last', name='block3_pool'),
        # Block 4
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv1'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv2'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv3'),
        MaxPooling2D(pool_size=(pool_size, pool_size), data_format='channels_last', name='block4_pool'),
        # Block 5
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv1'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv2'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv3'),
        MaxPooling2D(pool_size=(pool_size, pool_size), data_format='channels_last', name='block5_pool'),
    ]

    decoding_layers = [
        # Block 5 decode
        UpSampling2D(size=(pool_size, pool_size), data_format='channels_last'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv3_decode'),
        BatchNormalization(),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv2_decode'),
        BatchNormalization(),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block5_conv1_decode'),
        BatchNormalization(),
        # Block 5=4 decode
        UpSampling2D(size=(pool_size, pool_size), data_format='channels_last'),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv3_decode'),
        BatchNormalization(),
        Conv2D(512, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv2_decode'),
        BatchNormalization(),
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block4_conv1_decode'),
        BatchNormalization(),
        # Block 3 decode
        UpSampling2D(size=(pool_size, pool_size), data_format='channels_last'),
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv3_decode'),
        BatchNormalization(),
        Conv2D(256, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv2_decode'),
        BatchNormalization(),
        Conv2D(128, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block3_conv1_decode'),
        BatchNormalization(),
        # Block 2 decode
        UpSampling2D(size=(pool_size, pool_size), data_format='channels_last'),
        Conv2D(128, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block2_conv2_decode'),
        BatchNormalization(),
        Conv2D(64, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block2_conv1_decode'),
        BatchNormalization(),
        # Block 1 decode
        UpSampling2D(size=(pool_size, pool_size), data_format='channels_last'),
        Conv2D(64, (3, 3), activation='relu', padding='same', data_format='channels_last', name='block1_conv2_decode'),
        BatchNormalization(),
        Conv2D(nb_classes, (1, 1), padding='valid', data_format='channels_last', name='block1_conv1_decode'),
        BatchNormalization(),
    ]

    # Creation of a sequential model
    segnet_basic = Sequential()

    # Addition of the encoding layers
    segnet_basic.add(Layer(input_shape=(img_size, img_size, 3)))
    segnet_basic.encoding_layers = encoding_layers
    for l in segnet_basic.encoding_layers:
        segnet_basic.add(l)

    # Loads VGG16 weights
    # segnet_basic.summary()
    segnet_basic.load_weights(vgg_weights_path)

    # Addition of the decoding layers
    segnet_basic.decoding_layers = decoding_layers
    for l in segnet_basic.decoding_layers:
        segnet_basic.add(l)

    # Add softmax activation
    segnet_basic.add(Activation('softmax'))
    # segnet_basic.summary()

    if save:
        # Save model
        model_filename = "segnet_vgg16_{}_{}.h5".format(img_size, nb_classes)
        segnet_basic.save(model_filename)
    return segnet_basic


def train_model(model, train_data, train_label, val_data, val_label, model_name="model.h5", save=True, plot=True):
    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])
    model_fitted = model.fit(train_data,
                             train_label,
                             epochs=20,
                             batch_size=20,
                             validation_data=(val_data, val_label))
    # Save model
    if save:
        model.save(model_name)
    # Plotting the results
    if plot:
        plot_validation_info_kfold(model_fitted)


# ---------------------- Mapillary Dataset -----------------------------------------------------------------------------
def reclass_mapillary_2_snow(arr_in):
    """
    Reclass the mapillary categories into new categories
    :param arr_in:
    :return:
    """
    not_snow = [0, 1, 7, 11, 12, 15, 20, 25, 26, 29, 30, 31, 33, 36, 52, 53, 9, 13, 14, 16, 17, 18, 21, 23, 37, 38, 39,
                40, 41, 42, 43, 54, 55, 56, 57, 58, 60, 61, 2, 3, 4, 5, 6, 8, 10, 19, 22, 24, 32, 34, 35, 44, 45, 46,
                47, 48, 49, 50, 51, 59, 62, 63, 64, 65, 27]
    snow = [28]

    arr_flat = arr_in.mean(axis=2, dtype=int).reshape(arr_in.shape[0], arr_in.shape[1], 1)
    arr = arr_flat.copy()
    arr[np.isin(arr_flat, not_snow)] = 0
    arr[np.isin(arr_flat, snow)] = 1
    return arr


def prep_mapillary(data_folder, width, height, nb_classes):
    """
    Create npy file for train, validate and test image sets
    :param data_folder:
    :param width:
    :param height:
    :param nb_classes:
    :return:
    """
    train_folder = data_folder
    valid_folder = data_folder
    print("Processing :")
    val_data, val_label = prep_data_mapillary(valid_folder, height, width, nb_classes, mode="validation")
    # train_data, train_label = prep_data_mapillary(train_folder, height, width, nb_classes, mode="training")
    train_data, train_label = prep_data_mapillary(train_folder, height, width, nb_classes, mode="testing")

    return train_data, train_label, val_data, val_label


def prep_data_mapillary(data_folder, width, height, nb_classes, mode):
    data = []
    label_liste = []
    img_dir = data_folder + mode + "/images/"
    lab_dir = data_folder + mode + "/instances/"
    images = os.listdir(img_dir)
    print(images)
    labels = os.listdir(lab_dir)
    # Images processing
    print("Loading {} images:".format(mode))
    pbar = progressbar.ProgressBar()
    for image in pbar(images):
        img = cv2.imread(img_dir + image)
        img_resized = cv2.resize(img, (width, height))
        img_norm = normalized(img_resized)
        data.append(img_norm)
    print("Saving {} images npy".format(mode))
    np.save(data_folder + "npy/{}_data_{}_{}_{}".format(mode, height, width, nb_classes), np.array(data))

    # Labels processing
    print("Loading {} labels:".format(mode))
    pbar2 = progressbar.ProgressBar()
    for label in pbar2(labels):
        l_img = cv2.imread(lab_dir + label)
        l_img = cv2.resize(l_img, (width, height), interpolation=cv2.INTER_NEAREST).astype(dtype=np.int8)
        l_img = reclass_mapillary_2_snow(l_img)
        l_img = one_hot_it(l_img, width, height, nb_classes)
        label_liste.append(l_img)

    print("Saving {} labels npy".format(mode))
    np.save(data_folder + "npy/{}_label_{}_{}_{}".format(mode, height, width, nb_classes), np.array(label_liste))
    return np.array(data), np.array(label_liste)






if __name__ == "__main__":
    # ------------------------------------------------------------------------------------------------------------------
    # Variables initialization
    # ------------------------------------------------------------------------------------------------------------------
    VGG_Weights_path = r'D:/Guillaume/Ottawa-master/Data-Raw-Template/Segmentation/Models/vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5'
    mapillary_path = r'D:/Guillaume/Ottawa-master/Data-Raw-Template/Segmentation/Mapillary-vistas-dataset/'

    height = 256
    width = 256
    nb_classes = 2

    # ------------------------------------------------------------------------------------------------------------------
    # Run functions
    # ------------------------------------------------------------------------------------------------------------------

    # Build model
    model_snow = vgg_segnet(nb_classes, height, width, VGG_Weights_path, True)
    # model_snow = load_model("D:/Guillaume/Ottawa-master/Data-Raw-Template/Segmentation/Models/vgg16_256_256_2.h5")

    # Build training data set
    # prep_mapillary(mapillary_path, width, height, nb_classes)

    npy_path = os.path.join(mapillary_path, "npy", "snow_2_classes_256")
    train_data = np.load(os.path.join(npy_path, "training_data_256_256_2.npy"))
    train_label = np.load(os.path.join(npy_path, "training_label_256_256_2.npy"))
    val_data = np.load(os.path.join(npy_path, "validation_data_256_256_2.npy"))
    val_label = np.load(os.path.join(npy_path, "validation_label_256_256_2.npy"))

    # Training
    train_model(model_snow, train_data, train_label, val_data, val_label, model_name="trained_model_snow_2_classes_256.h5", save=True, plot=True)
    
    # Evaluating on testing set
    model = load_model("trained_model_snow_2_classes_256.h5")
    test_data = np.load(os.path.join(npy_path, "testing_data_256_256_2.npy"))
    test_label = np.load(os.path.join(npy_path, "testing_label_256_256_2.npy"))
    model.evaluate(test_data, test_label)


    #  Predictions
    # img_sample_folder = "D:/Guillaume/Ottawa-master/Data-Raw-Template/Photo/All_mapillary_jpg/"
    # sample_img = prep_images_folder(img_sample_folder, width, height, nb_classes)
    # predictions_sample = model_sky.predict(sample_img, verbose=1)
    # np.save("D:/Guillaume/Ottawa-master/Data-Raw-Template/Photo/npy/predictions_all_mapillary_128_128_4.npy", predictions_sample)



