from PIL import Image, ImageChops
import numpy as np

# Minimal placeholder swap: place images side-by-side with a separator

def simple_face_swap(path1: str, path2: str, out_path: str):
    img1 = Image.open(path1).convert('RGBA')
    img2 = Image.open(path2).convert('RGBA')

    # Resize to same height (max height) while keeping aspect
    h = max(img1.height, img2.height)
    w1 = int(img1.width * (h / img1.height))
    w2 = int(img2.width * (h / img2.height))
    img1 = img1.resize((w1, h), Image.ANTIALIAS)
    img2 = img2.resize((w2, h), Image.ANTIALIAS)

    sep = 10
    out = Image.new('RGBA', (w1 + w2 + sep, h), (255,255,255,255))
    out.paste(img1, (0,0))
    out.paste(img2, (w1 + sep, 0))
    out.convert('RGB').save(out_path, format='PNG')
    return out_path

# ---------------- Real Face Swap implementation (requires dlib, OpenCV, predictor) ----------------
import cv2
import dlib
import os


def _get_landmarks(img, detector, predictor):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 1)
    if len(rects) == 0:
        return None
    rect = max(rects, key=lambda r: r.width() * r.height())
    shape = predictor(gray, rect)
    coords = np.array([[p.x, p.y] for p in shape.parts()], dtype=np.float32)
    return coords


def real_face_swap(src_path: str, dst_path: str, out_path: str, predictor_path: str = None):
    if predictor_path is None:
        predictor_path = os.path.join(os.path.dirname(__file__), 'shape_predictor_68_face_landmarks.dat')
    if not os.path.exists(predictor_path):
        raise FileNotFoundError(
            f"Landmark predictor not found: {predictor_path}. Please download shape_predictor_68_face_landmarks.dat and place it next to this script."
        )

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    src_img = cv2.imread(src_path)
    dst_img = cv2.imread(dst_path)
    if src_img is None or dst_img is None:
        raise ValueError("Failed to load input images.")

    pts_src = _get_landmarks(src_img, detector, predictor)
    pts_dst = _get_landmarks(dst_img, detector, predictor)
    if pts_src is None or pts_dst is None:
        raise ValueError("Could not detect a face in one or both images.")

    # Build 3-point similarity transform using eyes and nose tip
    left_eye_src = np.mean(pts_src[36:42], axis=0)
    right_eye_src = np.mean(pts_src[42:48], axis=0)
    nose_src = pts_src[30]

    left_eye_dst = np.mean(pts_dst[36:42], axis=0)
    right_eye_dst = np.mean(pts_dst[42:48], axis=0)
    nose_dst = pts_dst[30]

    src_tri = np.array([left_eye_src, right_eye_src, nose_src], dtype=np.float32)
    dst_tri = np.array([left_eye_dst, right_eye_dst, nose_dst], dtype=np.float32)

    M = cv2.getAffineTransform(src_tri, dst_tri)

    h, w = dst_img.shape[:2]
    warped_src = cv2.warpAffine(src_img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    # Transform all source landmarks to destination coordinate space
    pts_src_h = np.hstack([pts_src, np.ones((pts_src.shape[0], 1))])  # 68x3
    transformed_pts = pts_src_h.dot(M.T)
    pts_dst_hat = transformed_pts.astype(np.int32)

    # Mask of destination face region
    hull = cv2.convexHull(pts_dst_hat)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)

    # Blend: warp source to destination, then apply mask
    warped_face = warped_src
    masked_warp = cv2.bitwise_and(warped_face, warped_face, mask=mask)
    inv_mask = cv2.bitwise_not(mask)
    background = cv2.bitwise_and(dst_img, dst_img, mask=inv_mask)
    result = cv2.add(background, masked_warp)

    # Attempt seamless cloning for smoother blend (fallback if it fails)
    try:
        center = (w // 2, h // 2)
        result = cv2.seamlessClone(masked_warp, dst_img, mask, center, cv2.NORMAL_CLONE)
    except Exception:
        pass

    cv2.imwrite(out_path, result)
    return out_path
