import cv2
import numpy as np

# DirectShow camera
from camera import Camera

class Marker():
    def __init__(self, diff, box):
        # box is OpenCV RotatedRect
        self.center = tuple(map(int, box[0]))
        self.size = box[1]
        self.area = self.size[0] * self.size[1]

        # difference between marker and ellipse
        self.diff = diff
    
    def __repr__(self):
        return repr((self.center, self.area))

def get_ROI(markers, img):
    """
        get region of interest (region with fluorescence) 
        confined by four surrounding markers (x2, y2), (x3, y3), (x5, y5), (x4, y4).
        2 * dis(p2 - p0) = dis(p4 - p0)
        2 * dis(p3 - p1) = dis(p5 - p1)

        (x2, y2) - - - - - - - - (x3, y3)
           |        Region          |
        (x0, y0) - - - - - - - - (x1, y1)
           |          Of            |
           |       Interest         |
        (x4, y4) - - - - - - - - (x5, y5)
    """

    h, w = img.shape[:2]

    (x0, y0) = markers[0].center
    (x1, y1) = markers[1].center
    (x2, y2) = markers[2].center
    (x3, y3) = markers[3].center

    # extend the roi 
    x4 = x0 + 2 * (x0 - x2)
    y4 = y0 + 2 * (y0 - y2)
    # when coordinates are out of range
    if x4 > w:
        x4 = w - 1
    elif x4 < 0:
        x4 = 0
    if y4 > h:
        y4 = h - 1
    elif y4 < 0:
        y4 = 0
    x5 = x1 + 2 * (x1 - x3)
    y5 = y1 + 2 * (y1 - y3)
    if x5 > w:
        x5 = w - 1
    elif x5 < 0:
        x5 = 0
    if y5 > h:
        y5 = h - 1
    elif y5 < 0:
        y5 = 0
    
    # floodfill four ellipse markers 
    centers = [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]
    mask = np.zeros((h+2, w+2), np.uint8)
    for center in centers:
        cv2.floodFill(img, mask, center, 0)

    # make mask with ROI filled with 1
    mask = np.zeros((h, w), np.uint8)
    convex_poly = np.array([[x2, y2], [x3, y3], [x5, y5], [x4, y4]])
    cv2.fillConvexPoly(mask, convex_poly, 1)

    roi = img * mask

    # maybe use pseudocolor
    roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
    return roi

def normalize_blob(bw, center, size, angle, dsize):
    """
        straighten the rotateed ellipse blob, 
        and resize it to the same size.
    """

    # rotate
    m = cv2.getRotationMatrix2D(center, angle, 1.0)
    # translate
    m[0][2] -= center[0] - size[0] / 2
    m[1][2] -= center[1] - size[1] / 2

    blob = cv2.warpAffine(bw, m, size, flags=cv2.INTER_NEAREST)
    n_blob = cv2.resize(blob, dsize, interpolation=cv2.INTER_NEAREST)

    return n_blob

def is_marker(bw, contour, dsize=(50, 50)):
    """
        compare blob with standard ellipse,
        and calculate the number of pixels with different value.
    """

    # standard circle
    s_circle = np.zeros(dsize, np.uint8)
    cv2.circle(s_circle, (dsize[0]/2, dsize[1]/2), dsize[0]/2, 255, -1)

    # fit ellipse
    box = cv2.fitEllipse(contour)

    # compare the difference
    size = tuple(map(int, box[1]))
    n_blob = normalize_blob(bw, box[0], size, box[2], dsize)
    diff = cv2.absdiff(s_circle, n_blob).sum() / 255

    return diff, box

def find_contours(img):
    """
        find all contours with area between 100 and 15000 in an image.
        binarized: binary image
        contours: contour list
    """

    st = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        rval, bw = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    else:
        bw = img
    bw = cv2.morphologyEx(bw, cv2.MORPH_ERODE, st, iterations=1)
    contours, hierarchy = cv2.findContours(bw.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # only select contours with appropriate area
    contours = filter(lambda x:100 < cv2.contourArea(x) and len(x) > 5, contours)

    return bw, contours

def sort_markers(markers):
    """sort four markers by area and coordinate."""

    # sort by area
    markers.sort(key=lambda x:x.area)
    if markers[0].center[1] + markers[1].center[1] \
            > markers[2].center[1] + markers[3].center[1]:
        # big markers are above small ones
        if markers[0].center[0] > markers[1].center[0]:
            markers[0], markers[1] = markers[1], markers[0]
        if markers[2].center[0] > markers[3].center[0]:
            markers[2], markers[3] = markers[3], markers[2]
    else:
        if markers[0].center[0] < markers[1].center[0]:
            markers[0], markers[1] = markers[1], markers[0]
        if markers[2].center[0] < markers[3].center[0]:
            markers[2], markers[3] = markers[3], markers[2]

def find_markers(img):
    """
        find all markers and return 
        markers: list of Marker object
    """

    bw, contours = find_contours(img)

    markers = []
    for contour in contours:
        diff, box = is_marker(bw, contour)
        if diff < 350:
            markers.append(Marker(diff, box))

    if len(markers) < 4:
        return None

    # sort markers by its similarity to ellipse
    markers = sorted(markers, key=lambda x:x.diff)[:4]

    return markers

def transform_img(img, src_points, dst_points):
    """warp perspective transformation."""

    h, w = img.shape[:2]
    m = cv2.getPerspectiveTransform(src_points, dst_points)
    transformed = cv2.warpPerspective(img, m, (w, h))
    return transformed

def img_registration(src, dst, markers=None, display_fluorescence=False):
    """
        image registration between src image and dst image.
        if markers is not None, then suppose the markers are fixed 
    """

    if not markers:
        # src image processing
        markers = find_markers(src)
        if len(markers) is not 4:
            print 'cannot find 4 markers in source image'
            return dst

    # sort markers to a specific order
    sort_markers(markers)

    # if src is color image, convert it to binary image
    if src.ndim == 3:
        gray = cv2.cvtColor(src, cv2.COLOR_BGRA2GRAY)
        rval, bw = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    else:
        bw = src

    # get the region within markers
    roi = get_ROI(markers, bw)
    if display_fluorescence:
        cv2.imshow('fluorescence', roi)

    src_points = np.array(map(lambda x:map(int, x.center), markers), np.float32)

    # dst image process
    markers = find_markers(dst)
    if not markers:
        return dst

    sort_markers(markers)
    dst_points = np.array(map(lambda x:map(int, x.center), markers), np.float32)

    transformed = transform_img(roi, src_points, dst_points)

    # merge fluorescence image with camera color image
    merged = cv2.add(transformed, dst)
    return merged

def video_registration():
    src = cv2.imread('template.jpg')

    # open camera
    cam = cv2.VideoCapture(0)
    if cam.isOpened():
        rval, frame = cam.read()
    else:
        rval = False

    cv2.namedWindow('demo', cv2.CV_WINDOW_AUTOSIZE)
    while rval:
        rval, dst = cam.read()
        merged = img_registration(src, dst)
        cv2.imshow('demo', merged)
        key = cv2.waitKey(20)
        if key == 27:
                break

    cv2.destroyAllWindows()

#def video_registration(display_original=False, display_fluorescence=False):
    #template = cv2.imread('template.jpg')
    #src = template.copy()

    #markers= find_markers(template)
    #if len(markers) is not 4:
        #print 'cannot find 4 markers in template image'
        #return

    ## open cameras
    #usb_cam = Camera(0)
    #if not usb_cam.is_open():
        #print 'cannot open usb camera'
        #return
    #fluo_cam = Camera(2)
    #if not fluo_cam.is_open():
        #print 'cannot open fluorescence camera'
        #return

    #cv2.namedWindow('merged', cv2.CV_WINDOW_AUTOSIZE)
    #if display_original:
        #cv2.namedWindow('original', cv2.CV_WINDOW_AUTOSIZE)
    #if display_fluorescence:
        #cv2.namedWindow('fluorescence', cv2.CV_WINDOW_AUTOSIZE)

    #while True:
        #dst = usb_cam.read()
        #src = fluo_cam.read()
        #if display_original:
            #cv2.imshow('original', dst)
        #merged = img_registration(src, dst, markers, display_fluorescence)
        #cv2.imshow('demo', merged)
        #key = cv2.waitKey(20)
        #if key == 27:
            #break

    #cv2.destroyAllWindows()

if __name__ == '__main__':
    video_registration()
