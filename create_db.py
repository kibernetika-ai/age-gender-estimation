import argparse
import os

import h5py
import numpy as np
import cv2
import scipy.io
from tqdm import tqdm

from utils import get_meta


def get_args():
    parser = argparse.ArgumentParser(description="This script cleans-up noisy labels "
                                                 "and creates database for training.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--output", "-o", type=str, required=True,
                        help="path to output database mat file")
    parser.add_argument("--db", type=str, default="wiki",
                        help="dataset; wiki or imdb")
    parser.add_argument("--db-path", help="Path to the db dir if needed")
    parser.add_argument("--img_size", type=int, default=32,
                        help="output image size")
    parser.add_argument("--h5", action='store_true',
                        help="Save as hdf5 format")
    parser.add_argument("--min_score", type=float, default=1.0,
                        help="minimum face_score")
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    output_path = args.output
    db = args.db
    img_size = args.img_size
    min_score = args.min_score

    if args.db_path:
        root_path = args.db_path
    else:
        root_path = "data/{}_crop/".format(db)
    mat_path = os.path.join(root_path, "{}.mat".format(db))

    full_path, dob, gender, photo_taken, face_score, second_face_score, age = get_meta(mat_path, db)

    out_genders = []
    out_ages = []
    sample_num = len(face_score)
    out_imgs = np.empty((sample_num, img_size, img_size, 3), dtype=np.uint8)
    valid_sample_num = 0

    print(f"root_path = {root_path}")

    for i in tqdm(range(sample_num)):
        if face_score[i] < min_score:
            continue

        if (~np.isnan(second_face_score[i])) and second_face_score[i] > 0.0:
            continue

        if ~(0 <= age[i] <= 100):
            continue

        if np.isnan(gender[i]):
            continue

        out_genders.append(int(gender[i]))
        out_ages.append(age[i])
        img_path = os.path.join(root_path, str(full_path[i][0]))
        # print(f"Read {img_path}")
        img = cv2.imread(img_path)
        out_imgs[valid_sample_num] = cv2.resize(img, (img_size, img_size))
        valid_sample_num += 1

    print(f"Saving {len(out_imgs)} items")

    if args.h5:
        base, ext = os.path.splitext(output_path)
        output_path = base + '.h5'
        h5 = h5py.File(output_path, mode='w')
        h5.create_dataset('image', data=out_imgs[:valid_sample_num])
        h5.create_dataset('gender', data=np.array(out_genders))
        h5.create_dataset('age', data=np.array(out_ages))
        h5.attrs['db'] = db
        h5.attrs['img_size'] = img_size
        h5.attrs['min_score'] = min_score
        h5.close()

        print(f"Data has been written to {output_path}.")
    else:
        output = {"image": out_imgs[:valid_sample_num], "gender": np.array(out_genders), "age": np.array(out_ages),
                  "db": db, "img_size": img_size, "min_score": min_score}
        scipy.io.savemat(output_path, output, do_compression=True)


if __name__ == '__main__':
    main()
