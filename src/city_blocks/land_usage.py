import math
import numpy as np
from matplotlib.path import Path
from src.utilities import read_tif_file

# INPUT:    List, numpy.Array
# OUTPUT:   List
# Create a meshgrid (rectangular grid of unique x and y values) based on the
# land_use_array shapes (matches the input image). Flatten each x and y arrays
# to one-dimensional arrays and take the transposed vstack (concatenate the
# first axis after 1-D arrays of shape (N,) have been reshaped to (1,N)).
# Iterate through all found polygons. For each polygon, find the positions for
# every vertex making up the polygon. Make a path combining every position. Make
# a bool array which is True if the path contains the corresponding point from
# the meshgrid using https://matplotlib.org/api/path_api.html#matplotlib.path.Path.contains_points.
# Return the indices from the mask and extract the inner coordinates. Convert
# these to a np.array and randomly sample N% of the coordinates making up the
# polygon. Extract the colour of each sampled coordinate against the
# land_use_array. The type of land use most common in the sample will be the
# type of land use assigned to the polygon. Meshgrid implementation inspired:
# by https://stackoverflow.com/a/45731214
def get_land_usage(polygons, config, N=2):
    x, y = np.meshgrid(np.arange(config.land_use_array.shape[0]), np.arange(config.land_use_array.shape[1]))
    x, y = x.flatten(), y.flatten()
    points = np.vstack((x, y)).T

    # Extract the density array once; re-use for every polygon.
    density_array = read_tif_file(config.population_density_image_name)
    
    polygon_results = []
    for polygon in polygons:
        positions = [(int(round(vertex.position[0])), int(round(vertex.position[1]))) for vertex in polygon]
        path = Path(positions)
        grid = path.contains_points(points)
        mask = grid.reshape(config.land_use_array.shape[0], config.land_use_array.shape[1])
        indices = np.where(mask)

        inner_coords = np.array(list(zip(indices[0], indices[1])))

        random_indices = np.random.choice(inner_coords.shape[0], math.ceil(len(inner_coords) / N), replace=False)
        random_coords = inner_coords[random_indices]
        
        land_usages = {
            "residential" : 0,
            "commercial" : 0,
            "industry" : 0
        }

        for coord in random_coords:
            sample = list(config.land_use_array[coord[1]][coord[0]])
            if sample in config.residential_legend:
                land_usages["residential"] += 1
            elif sample in config.commercial_legend:
                land_usages["commercial"] += 1
            elif sample in config.industry_legend:
                land_usages["industry"] += 1

        final_use = max(land_usages, key=land_usages.get)
        density = get_population_density(random_coords, config, density_array)

        polygon_results.append({"polygon" : polygon, "land_usage" : final_use, "population_density" : density})

    return polygon_results


# INPUT:    List, Config
# OUTPUT:   List
def get_population_density(indices, config, density_array):
    population_density = []
    for index in indices:
        scaled_x = int(round(index[0] * density_array.shape[0] / config.land_use_array.shape[0]))
        scaled_y = int(round(index[1] * density_array.shape[1] / config.land_use_array.shape[1]))
        density = density_array[scaled_x, scaled_y]
        population_density.append(density)

    # Return the average population desnsity.
    return sum(population_density) / float(len(population_density))