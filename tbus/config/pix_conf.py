#
# Sensor pixel arrangement configuration
#

# The number of modules in image row
modules_in_row = 4

# The module pixels arrangement in terms of channel indexes
mod_pixels = (
	( 3,  4,  5,  6,  7,  8,  9, 10),
	(11, 12, 13, 14, 15, 16, 17, 18),
	(19, 20, 21, 22, 23, 24, 25, 26),
	(27, 28, 29, 30, 31, 32, 33, 34)
)

# The module area width and height calculated from the above definition
mod_w = len(mod_pixels[0])
mod_h = len(mod_pixels)

# Get the (module_index, module_origin) tuple given the pixel row, column along with the total number of modules.
# The module_origin is the tuple containing the minimum row, column values of the module pixels (module's top left corner).
def __plain_mod_resolver(r, c, nmodules):
	i, j = r // mod_h, c // mod_w
	return i * modules_in_row + j, (i * mod_h, j * mod_w)

# Use you own implementation if necessary
mod_resolver = __plain_mod_resolver

# The following transformation may be applied to the resulting image
# in the order they are described.

# Flip image in left-right direction
# image_fliplr = True
image_fliplr = False

# Flip image in up-down direction
# image_flipud = True
image_flipud = False

# Transpose the resulting image so rows will become columns and vise versa
# image_transpose = True
image_transpose = False

#
# The channel data preprocessing function. Several examples are below.
#
# The simplest form - no channel processing:
def __plain_channel_data(d, m, c): return d[m, c]

#channel_data = __plain_channel_data

# Use you own implementation if necessary
channel_data = lambda d, m, c: -d[m, c]
