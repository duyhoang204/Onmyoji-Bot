from imagesearch import region_grabber
import cv2
import numpy as np

def test():
    from matplotlib import pyplot as plt
    cv = cv2
    # img = cv.imread('test.png', 0)
    im = region_grabber(region=(688, 436, 950, 496))
    img = np.array(im)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    im.save('testarea.png')
    img2 = img.copy()
    template = cv.imread('images/buff_exp_100.png', 0)
    w, h = template.shape[::-1]
    # All the 6 methods for comparison in a list
    methods = methods = ['cv.TM_CCOEFF_NORMED']
    for meth in methods:
        img = img2.copy()
        method = eval(meth)
        # Apply template Matching
        res = cv.matchTemplate(img, template, method)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
        if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv.rectangle(img, top_left, bottom_right, 255, 2)
        plt.subplot(121), plt.imshow(res, cmap='gray')
        plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
        plt.subplot(122), plt.imshow(img, cmap='gray')
        plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
        plt.suptitle(meth)
        plt.show()

test()