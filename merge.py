import cv2
import numpy as np
from PIL import Image


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

#def get_ROI(markers, img):
    #"""
        #get region of interest (region with fluorescence) 
        #confined by four surrounding markers (x2, y2), (x3, y3), (x5, y5), (x4, y4).
        #2 * dis(p2 - p0) = dis(p4 - p0)
        #2 * dis(p3 - p1) = dis(p5 - p1)

        #(x2, y2) - - - - - - - - (x3, y3)
           #|        Region          |
        #(x0, y0) - - - - - - - - (x1, y1)
           #|          Of            |
           #|       Interest         |
        #(x4, y4) - - - - - - - - (x5, y5)
    #"""

    #h, w = img.shape[:2]

    #(x0, y0) = markers[0].center
    #(x1, y1) = markers[1].center
    #(x2, y2) = markers[2].center
    #(x3, y3) = markers[3].center

    ## extend the roi 
    #x4 = x0 + 2 * (x0 - x2)
    #y4 = y0 + 2 * (y0 - y2)
    ## when coordinates are out of range
    #if x4 > w:
        #x4 = w - 1
    #elif x4 < 0:
        #x4 = 0
    #if y4 > h:
        #y4 = h - 1
    #elif y4 < 0:
        #y4 = 0
    #x5 = x1 + 2 * (x1 - x3)
    #y5 = y1 + 2 * (y1 - y3)
    #if x5 > w:
        #x5 = w - 1
    #elif x5 < 0:
        #x5 = 0
    #if y5 > h:
        #y5 = h - 1
    #elif y5 < 0:
        #y5 = 0
    
     ##floodfill four ellipse markers 
    #centers = [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]
    #mask = np.zeros((h+2, w+2), np.uint8)
    #for center in centers:
        #cv2.floodFill(img, mask, center, 0)

    ## make mask with ROI filled with 1
    #mask = np.zeros((h, w), np.uint8)
    #convex_poly = np.array([[x2, y2], [x3, y3], [x5, y5], [x4, y4]])
    #cv2.fillConvexPoly(mask, convex_poly, 1)

    #roi = img * mask

     ##maybe use pseudocolor
    #roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
    #return roi


def normalize_blob(bw, center, size, angle, dsize):
    """straighten the rotateed ellipse blob, 
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
    """compare blob with standard ellipse,
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
    if img.ndim != 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    rval, bw = cv2.threshold(img, 0, 255, 
                            cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    st = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_ERODE, st, iterations=1)
    contours, hierarchy = cv2.findContours(bw.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # only select contours with appropriate area
    contours = filter(lambda x: 100 < cv2.contourArea(x) and len(x) > 5, contours)

    return bw, contours


def sort_markers(markers):
    """sort four markers by area and coordinate."""

    # sort by area
    markers.sort(key=lambda x: x.area)
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
    """find all markers and return 
    markers: list of Marker object.
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
    markers = sorted(markers, key=lambda x: x.diff)[:4]

    return markers


def transform_img(img, src_points, dst_points, (h, w)):
    """warp perspective transformation."""

    m = cv2.getPerspectiveTransform(src_points, dst_points)
    transformed = cv2.warpPerspective(img, m, (w, h))
    return transformed


def merge_img(dst, mask):
    """convert into color image;
    apply mask (transformed fluorescence image) to dst image;
    """
    h, w = dst.shape
    green = np.zeros((h, w, 3), np.uint8)
    cv2.fillConvexPoly(green, np.array([[0, 0], [w, 0], [w, h], [0, h]]), (0, 255, 0))
    green_mask = cv2.multiply(green, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))

    inv_mask = cv2.bitwise_not(mask)
    dst_and = cv2.bitwise_and(dst, inv_mask)
    dst_color = cv2.cvtColor(dst_and, cv2.COLOR_GRAY2BGR)
    merged = cv2.add(dst_color, green_mask)
    return merged

def img_registration(src, dst, template, outputmode='PIL'):
    """image registration between src image and dst image
    according to four markers in template image.
    input images can be color or grayscale images, 'OpenCV' or 'PIL'
    return a pseudo-color image with format either in 'OpenCV' or 'PIL' 
    """
    
    if type(src) != np.array and 'PIL' in str(src):
        src = pil_cv(pil_img=src)
    if type(dst) != np.array and 'PIL' in str(dst):
        dst = pil_cv(pil_img=dst)
    if type(template) != np.array and 'PIL' in str(template):
        template = pil_cv(pil_img=template)

    if src.ndim != 2:
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    if dst.ndim != 2:
        dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)

    ############################################

    markers = find_markers(template)
    if not markers:
        raise ValueError('cannot find markers in template image')

    sort_markers(markers)
    src_points = np.array(map(lambda x: map(int, x.center), markers), 
                         np.float32)

    rval, src_bw = cv2.threshold(src, 0, 255, 
                                cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    st = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    src_bw = cv2.morphologyEx(src_bw, cv2.MORPH_ERODE, st, iterations=1)

    ############################################

    markers = find_markers(dst)
    if markers:
        sort_markers(markers)
        dst_points = np.array(map(lambda x: map(int, x.center), markers), 
                             np.float32)

        dst_size = dst.shape
        transformed_mask = transform_img(src_bw, src_points, 
                                         dst_points, dst_size)

        merged = merge_img(dst, transformed_mask)
    else:
        merged = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)

    if outputmode == 'OpenCV':
        return merged
    elif outputmode == 'PIL':
        return pil_cv(cv_img=merged)
    else:
        raise TypeError('outputmode error')

def pil_cv(pil_img=None, cv_img=None):
    """convert  PIL Image <=> OpenCV Image."""
    if pil_img:
        return np.array(pil_img)
    # elif cv_img: error
    elif cv_img != None:
        return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    else:
        raise TypeError('Please input an image')

def video_registration():
    """demo"""

    from camera import Camera

    # get all accessible cameras' name
    devices = []
    for i in range(10):
        cam = Camera(i)
        if cam.is_open():
            devices.append((i, cam.name))
        del cam
    
    # fluorescence camera's name is MV...
    fluo_cam = None
    for i, cam_name in devices:
        if cam_name.startswith('MV'):
            fluo_cam = Camera(i)
        else:
            print i, cam_name
    if not fluo_cam:
        print 'cannot open fluorescence camera'
        return

    # select usb camera
    while True:
        try:
            i = int(raw_input('Please selcet usb camera number: '))
            break
        except ValueError:
            print 'input error'
    usb_cam = Camera(i)

    cv2.namedWindow('merged', cv2.CV_WINDOW_AUTOSIZE)
    cv2.namedWindow('fluorescence', cv2.CV_WINDOW_AUTOSIZE)
   
    # save template file
    markers = []
    while True:
        template = fluo_cam.get_image(1)
        cv2.imshow('fluorescence', template)
        c = cv2.waitKey(30)
        if c == ord('s'):
            markers = find_markers(template)
            if len(markers) == 4:
                cv2.imwrite('template.jpg', template)
                break
        elif c == 27:
            break

    # read template image
    template = cv2.imread('template.jpg')
   
    while True:
        dst = usb_cam.get_image(1) 
        src = fluo_cam.get_image(1)
        
        merged = img_registration(src, dst, template)
        
        cv2.imshow('merged', merged)
        key = cv2.waitKey(30)
        if key == 27:
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    video_registration()
