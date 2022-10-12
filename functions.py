import numpy
from PIL import Image, ImageOps

# chars = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz'
startAsciiRange = 32
endAsciiRange = 122
chars = "".join([chr(x) for x in range(startAsciiRange, endAsciiRange + 1)])
defaultBase = 5
defaultResizeFactor = 10


def char_to_num(c, charMap=chars):
    if charMap:
        alpha = dict()
        for i, v in enumerate(charMap):
            alpha[v] = i
        try:
            return alpha[c]
        except KeyError:
            raise KeyError("%s not in charmap [%s]" % (c, chars))
    else:
        return ord(c)


def num_to_bits(x, base=defaultBase, numBits=None):
    if numBits and x >= (base**numBits):
        raise RuntimeError(
            "Insufficient bits to hold %i with base %i and %i bits. Raise base or numBits." % (x, base, numBits))
    digits = []
    while x:
        digits.append(x % base)
        x //= base
    if numBits:
        digits += [0] * (numBits - len(digits))
    digits.reverse()
    return digits


def char_to_bits(c, base=defaultBase, numBits=None, charMap=chars):
    try:
        return num_to_bits(char_to_num(c, charMap), base, numBits)
    except RuntimeError as e:
        print(e)
        raise RuntimeError("Unable to hold %c's position (%i) in charmap [%s] with base %i and %i bits. Raise base, numBits, or change charMap." % (
            c, charMap.find(c), charMap, base, numBits))


def line_to_bit_array(l, base=defaultBase, numBits=None, charMap=chars):
    # We need to figure out the numbits for the maximum char
    if numBits is None:
        maxChar = max([chars.find(c) for c in s])
        numBits = len(num_to_bits(maxChar, base))
    return [char_to_bits(c, base, numBits, charMap) for c in l]


def string_to_array(s, base=defaultBase, numBits=None, charMap=chars, isHorizontal=False, addSpaces=False):

    # Split the string by lines to see if it's a paragraph
    lines = s.splitlines()

    # If the string was a single line, it's easy!
    if len(lines) == 1:
        return numpy.array(line_to_bit_array(s, base, numBits, charMap), numpy.uint8)

    # Otherwise, we need to turn it into a matrix
    else:

        # Get the max line length
        maxLength = max([len(line) for line in lines])

        # Left align each line and pad with a space
        la = [("{0: <%i}" % maxLength).format(line) for line in lines]

        # Join them up into a large string
        joinedString = "".join(la)

        # Convert them to bits
        lineArray = numpy.array(line_to_bit_array(joinedString, base, numBits, charMap), numpy.uint8)

        # We can calculate the numBits from here, in case it wasn't specified
        if not numBits:
            numBits = lineArray.shape[1]

        # Image size: 1 char = 1 pixel
        numLines = len(la)
        numChars = len(la[0])

        # Reshape the array
        reshaped = numpy.array(lineArray).astype(numpy.uint8).reshape(numLines, numChars, numBits)

        if isHorizontal:
            returnMe = numpy.vstack([row.T for row in reshaped])
            if addSpaces:
                splitArray = numpy.vsplit(returnMe, returnMe.shape[0] // numBits)
                # Add spaces between the split sub-arrays
                returnMe = numpy.vstack([numpy.vstack([section, [0] * numChars]) for section in splitArray])[:-1]
        else:
            returnMe = numpy.hstack(reshaped)
            if addSpaces:
                splitArray = numpy.hsplit(returnMe, returnMe.shape[1] // numBits)
                # Add spaces between the split sub-arrays
                returnMe = numpy.hstack([numpy.vstack([numpy.hstack([item, [0]]) for item in section])
                                         for section in splitArray])[:, :-1]

        # Stack the array and return
        return returnMe


def string_to_image(s, base=defaultBase, numBits=None, charMap=chars, isHorizontal=False):
    arr = string_to_array(s, base, numBits, charMap, isHorizontal, True)
    scaled = scale_array(arr, base=base)
    return Image.fromarray(scaled, "L")


def scale_array(array, scale=255, base=defaultBase):
    return (array / float(base - 1) * float(scale)).astype(numpy.uint8)


def resize(image, resizeFactor=defaultResizeFactor):
    newWidth = image.size[1] * resizeFactor
    newHeight = image.size[0] * resizeFactor
    resized = image.resize((newHeight, newWidth), Image.Resampling.NEAREST)
    return resized


def border(image, color="black", width=1):
    return ImageOps.expand(image.convert("RGB"), border=width, fill=color)


def speech_bubble(s, base=defaultBase, numBits=None, charMap=chars, isHorizontal=False, fgColor="white", bgColor="black", resizeFactor=defaultResizeFactor):
    img = string_to_image(s, base, numBits, charMap, isHorizontal)
    img = ImageOps.colorize(img, bgColor, fgColor)
    img = border(img, bgColor)
    img = resize(img, resizeFactor)
    return img


if __name__ == '__main__':

    s = r"""In a field one summer's day a Grasshopper was
hopping about, chirping and singing to its heart's
content. An Ant passed by, bearing along with great
toil an ear of corn he was taking to the nest.
"Why not come and chat with me," said the Grasshopper,
"instead of toiling and moiling in that way?"

"I am helping to lay up food for the winter," said the
Ant, "and recommend you to do the same."

"Why bother about winter?" said the Grasshopper; we
have got plenty of food at present." But the Ant went
on its way and continued its toil.

When the winter came the Grasshopper found itself
dying of hunger, while it saw the ants distributing,
every day, corn and grain from the stores they had
collected in the summer.

Then the Grasshopper knew..."""

# s = "".join([c for c in chars])

    alienGreen = (150, 200, 100)

    img1 = speech_bubble(s, fgColor=alienGreen)
    img2 = speech_bubble(s, fgColor="red", isHorizontal=True)
    img3 = speech_bubble(s, base=3, fgColor=(0, 128, 255))

    img1.save("img1.png")
    img2.save("img2.png")
    img3.save("img3.png")

    img4 = speech_bubble('We have 8 weeks to worry about prod.', fgColor="red")
    img4.save("img4.png")

    r = """Kraken
    Keyboards"""

    speech_bubble(r, isHorizontal=True, fgColor=alienGreen).save('kraken_keyboards.png')

    charMap = ' abcdefghijklmnopqrstuvwxyz/'
    speech_bubble('fremont keyboard by /u/dnlglsn', isHorizontal=True, base=2,
                  charMap=charMap, resizeFactor=16).save("fremont.png")
    speech_bubble(charMap, base=2, charMap=charMap).save("chars.png")
